"""Choose your TIFF, preview segmentation, and export particle measurements."""
import argparse
import json
from pathlib import Path


class OwnImageWindow:
    def __init__(self,root,path,args):
        import tkinter as tk
        from tkinter import ttk
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,NavigationToolbar2Tk
        from microscopy.user_images import inspect_tiff
        self.root=root;self.path=Path(path);self.args=args;self.last_run=None
        root.title('TEM Particle Lab - analyse your own TIFF');root.geometry('1250x850')
        info=inspect_tiff(path);self.info=info
        sidebar=ttk.Frame(root,padding=5);sidebar.pack(side='left',fill='y')
        scroll_canvas=tk.Canvas(sidebar,width=310,highlightthickness=0)
        scrollbar=ttk.Scrollbar(sidebar,orient='vertical',command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=scrollbar.set);scrollbar.pack(side='right',fill='y');scroll_canvas.pack(side='left',fill='both',expand=True)
        control=ttk.Frame(scroll_canvas,padding=5);scroll_canvas.create_window((0,0),window=control,anchor='nw')
        control.bind('<Configure>',lambda event:scroll_canvas.configure(scrollregion=scroll_canvas.bbox('all')))
        scroll_canvas.bind('<Enter>',lambda event:scroll_canvas.bind_all('<MouseWheel>',lambda e:scroll_canvas.yview_scroll(int(-e.delta/120),'units')))
        scroll_canvas.bind('<Leave>',lambda event:scroll_canvas.unbind_all('<MouseWheel>'))
        viewer=ttk.Frame(root);viewer.pack(side='right',fill='both',expand=True)
        ttk.Label(control,text='Your TIFF particle analysis',font=('',12,'bold')).pack(anchor='w')
        ttk.Label(control,text=self.path.name,wraplength=265).pack(anchor='w',pady=5)
        ttk.Label(control,text=f"{len(info['pages'])} TIFF page(s).\nChoose the intended page/channel.\nNo silent stack projection or RGB averaging.",wraplength=265).pack(anchor='w',pady=5)
        self.values={};self.widgets={}
        def field(name,title,value,choices=None):
            row=ttk.Frame(control);row.pack(fill='x',pady=2)
            ttk.Label(row,text=title,width=20).pack(side='left')
            variable=tk.StringVar(value=str(value));self.values[name]=variable
            widget=ttk.Combobox(row,textvariable=variable,values=choices,width=13,state='readonly') if choices else ttk.Entry(row,textvariable=variable,width=15)
            widget.pack(side='right');self.widgets[name]=widget
        field('page','Page (zero-based)',args.page if args.page is not None else 0,[str(i) for i in range(len(info['pages']))])
        field('channel','Channel','Auto' if args.channel is None else args.channel,['Auto'])
        self.widgets['page'].bind('<<ComboboxSelected>>',lambda event:self.channel_choices())
        field('crop','Crop r0 r1 c0 c1','' if args.crop is None else ' '.join(map(str,args.crop)))
        ttk.Button(control,text='Load selected plane / crop',command=self.load).pack(fill='x',pady=5)
        self.plane_info=tk.StringVar();ttk.Label(control,textvariable=self.plane_info,wraplength=265).pack(anchor='w')
        field('polarity','Foreground',args.polarity,['dark','bright'])
        field('method','Particle separation',args.method,['connected','watershed'])
        field('gaussian_sigma','Gaussian sigma (px)',getattr(args,'gaussian_sigma',0))
        field('background_radius','Background half-window',getattr(args,'background_radius',0))
        ttk.Label(control,text='0 = off. Smoothing can blur boundaries.\nBackground correction changes threshold values.',wraplength=265).pack(anchor='w',pady=3)
        self.threshold=tk.DoubleVar(value=0)
        ttk.Label(control,text='Threshold: native intensity units').pack(anchor='w',pady=(6,0))
        self.scale=tk.Scale(control,variable=self.threshold,orient='horizontal',length=265,resolution=1)
        self.scale.pack(fill='x')
        field('min_area','Minimum area (px)',args.min_area)
        field('nm_per_pixel','nm/pixel (optional)','' if args.nm_per_pixel is None else args.nm_per_pixel)
        ttk.Label(control,text='Blank calibration = pixels only.\nOne scale assumes equal X/Y pixel size.',wraplength=265).pack(anchor='w',pady=3)
        field('window_size','Peak window (odd px)',args.window_size)
        field('min_peak_height','Minimum distance (px)',args.min_peak_height)
        field('min_seed_separation','Seed separation (px)',args.min_seed_separation)
        field('prominence','Peak prominence fraction',args.prominence)
        field('histogram_bins','Histogram bins',getattr(args,'histogram_bins',12))
        field('reference','Instance reference TIFF','' if getattr(args,'reference',None) is None else args.reference)
        ttk.Button(control,text='Choose optional reference',command=self.choose_reference).pack(fill='x',pady=3)
        ttk.Label(control,text='Seed controls apply to watershed only.\nConnected mode leaves touching objects merged.',wraplength=265).pack(anchor='w',pady=4)
        ttk.Button(control,text='Update segmentation preview',command=self.preview).pack(fill='x',pady=3)
        ttk.Button(control,text='Export measurements + report',command=self.export).pack(fill='x',pady=3)
        ttk.Button(control,text='Review exported particles',command=self.review).pack(fill='x',pady=3)
        ttk.Button(control,text='Manual endpoint measurements',command=self.manual_measurements).pack(fill='x',pady=3)
        ttk.Button(control,text='Open exported report',command=self.open_report).pack(fill='x',pady=3)
        self.message=tk.StringVar(value='Exclude scale bars and text with a crop. Predictions need boundary review.')
        ttk.Label(control,textvariable=self.message,wraplength=265).pack(anchor='w',pady=5)
        self.figure=Figure(figsize=(10,6),layout='constrained');self.axes=self.figure.subplots(1,4)
        self.canvas=FigureCanvasTkAgg(self.figure,master=viewer);self.canvas.get_tk_widget().pack(fill='both',expand=True)
        NavigationToolbar2Tk(self.canvas,viewer)
        self.initializing=True
        self.channel_choices(reset=False);self.load()
        self.initializing=False

    def channel_choices(self,reset=True):
        page=self.info['pages'][int(self.values['page'].get())]
        axes=[i for i,a in enumerate(page['axes']) if a in 'SC']
        choices=['Auto']+[str(i) for i in range(page['shape'][axes[0]])] if len(page['shape'])==3 and len(axes)==1 else ['Auto']
        self.widgets['channel']['values']=choices
        if reset or self.values['channel'].get() not in choices:self.values['channel'].set('Auto')

    def error(self,error):
        from tkinter import messagebox
        self.message.set(str(error));messagebox.showerror('Check image or settings',str(error),parent=self.root)

    def load(self):
        from microscopy.user_images import load_tiff_plane
        try:
            channel=self.values['channel'].get()
            self.plane,self.selection=load_tiff_plane(self.path,int(self.values['page'].get()),None if channel=='Auto' else int(channel))
            crop=self.values['crop'].get().strip()
            self.crop=[0,self.plane.shape[0],0,self.plane.shape[1]] if not crop else [int(i) for i in crop.split()]
            if len(self.crop)!=4:raise ValueError('Crop needs four integers: r0 r1 c0 c1 (stop endpoints excluded).')
            r0,r1,c0,c1=self.crop
            if not 0<=r0<r1<=self.plane.shape[0] or not 0<=c0<c1<=self.plane.shape[1]:raise ValueError('Crop exceeds selected plane.')
            self.loaded_selection=(self.values['page'].get(),channel,self.values['crop'].get())
            roi=self.plane[r0:r1,c0:c1]
            from microscopy.user_extensions import preprocess_image
            working,_,_=preprocess_image(roi,float(self.values['gaussian_sigma'].get()),int(self.values['background_radius'].get()),self.values['polarity'].get())
            lo,hi=float(working.min()),float(working.max())
            self.scale.configure(from_=lo,to=hi if hi>lo else lo+1,resolution=max((hi-lo)/1000,1e-6) if self.values['gaussian_sigma'].get()!='0' or self.values['background_radius'].get()!='0' or roi.dtype.kind=='f' else 1)
            self.threshold.set(self.args.threshold if self.args.threshold is not None and lo<=self.args.threshold<=hi else (lo+hi)/2)
            self.plane_info.set(f"Selected {roi.shape}, {roi.dtype}; range {lo:g} to {hi:g}.\nInitial midpoint is a starting guess, not validated segmentation.")
            self.preview()
        except (ValueError,OSError,ImportError) as error:
            if self.initializing:self.message.set(str(error).replace('Choose --channel INDEX','Select a Channel and click Load'))
            else:self.error(error)

    def settings(self):
        if not hasattr(self,'plane') or not hasattr(self,'loaded_selection'):raise ValueError('Load a valid plane and crop first.')
        current=(self.values['page'].get(),self.values['channel'].get(),self.values['crop'].get())
        if current!=self.loaded_selection:raise ValueError('Page/channel/crop changed. Click Load selected plane / crop first.')
        r0,r1,c0,c1=self.crop
        return dict(crop_rows=[r0,r1],crop_columns=[c0,c1],threshold=float(self.threshold.get()),
                    polarity=self.values['polarity'].get(),method=self.values['method'].get(),
                    min_area=int(self.values['min_area'].get()),window_size=int(self.values['window_size'].get()),
                    min_peak_height=float(self.values['min_peak_height'].get()),min_seed_separation=float(self.values['min_seed_separation'].get()),
                    prominence=float(self.values['prominence'].get()),gaussian_sigma=float(self.values['gaussian_sigma'].get()),
                    background_radius=int(self.values['background_radius'].get()),histogram_bins=int(self.values['histogram_bins'].get()),
                    link_fraction=getattr(self.args,'link_fraction',.1),min_match_iou=getattr(self.args,'min_match_iou',.5))

    def preview(self):
        import numpy as np
        from skimage.measure import regionprops,find_contours
        from microscopy.user_images import process_and_segment
        try:
            settings=self.settings();r0,r1,c0,c1=self.crop;roi=self.plane[r0:r1,c0:c1]
            processed,background,candidate,labels,notes,stats=process_and_segment(roi,settings)
            lo,hi=float(processed.min()),float(processed.max())
            previous_threshold=float(self.threshold.get())
            self.scale.configure(from_=lo,to=hi if hi>lo else lo+1,resolution=max((hi-lo)/1000,1e-6) if settings['gaussian_sigma'] or settings['background_radius'] or roi.dtype.kind=='f' else 1)
            self.threshold.set(previous_threshold if lo<=previous_threshold<=hi else (lo+hi)/2)
            if self.threshold.get()!=settings['threshold']:
                settings['threshold']=float(self.threshold.get())
                processed,background,candidate,labels,notes,stats=process_and_segment(roi,settings)
            for ax in self.axes:ax.clear();ax.set_axis_off()
            lo,hi=float(roi.min()),float(roi.max())
            self.axes[0].imshow(roi,cmap='gray',vmin=lo,vmax=hi);self.axes[0].set_title('Selected original plane')
            self.axes[1].imshow(processed,cmap='gray');self.axes[1].set_title('Processed working image')
            self.axes[2].imshow(candidate,cmap='gray',vmin=0,vmax=1);self.axes[2].set_title('Threshold foreground')
            self.axes[3].imshow(roi,cmap='gray',vmin=lo,vmax=hi);self.axes[3].set_title('Predictions: inspect outlines')
            regions=regionprops(labels)
            for p in regions:
                a,b,_,_=p.bbox
                for line in find_contours(np.pad(p.image,1),.5):self.axes[3].plot(line[:,1]+b-1,line[:,0]+a-1,color='cyan',lw=.8)
                rr,cc=p.centroid;self.axes[3].text(cc,rr,str(p.label),color='yellow',fontsize=8,clip_on=True)
            self.canvas.draw_idle();self.message.set(f"{len(regions)} predicted regions; {stats['seedless_foreground_pixels']} seedless foreground pixels. No reference validation. Exclude scale bars/text and review boundaries.")
        except (ValueError,OSError,ImportError) as error:self.error(error)

    def export(self):
        from microscopy.user_images import export_user_analysis
        try:
            settings=self.settings()
            text=self.values['nm_per_pixel'].get().strip();calibration=None if not text else float(text)
            self.last_run,summary=export_user_analysis(Path(__file__).resolve().parent,self.path,self.plane,self.selection,settings,calibration,
                                   'User-entered isotropic scale; not independently verified' if calibration is not None else 'not provided',
                                   reference_path=self.values['reference'].get().strip() or None)
            self.message.set('Saved '+self.last_run.name+'. Open report or review exported particles.');print('Report:',self.last_run/'report.html',flush=True)
        except (ValueError,OSError,ImportError) as error:self.error(error)

    def review(self):
        if self.last_run is None:self.error(ValueError('Export this analysis first.'));return
        from microscopy.particle_review import prepare_review
        from review_particles import ReviewWindow
        try:
            model,image=prepare_review(Path(__file__).resolve().parent,self.last_run,'own_image')
            window=ReviewWindow(model,image);window.fig.canvas.manager.show()
            self.review_window=window
        except (ValueError,OSError) as error:self.error(error)

    def open_report(self):
        if self.last_run is None:self.error(ValueError('Export this analysis first.'));return
        import webbrowser
        webbrowser.open((self.last_run/'report.html').as_uri())

    def choose_reference(self):
        from tkinter import filedialog
        path=filedialog.askopenfilename(parent=self.root,title='Aligned full-plane instance-label TIFF; 0 = background',filetypes=[('TIFF labels','*.tif *.tiff')])
        if path:self.values['reference'].set(path)

    def manual_measurements(self):
        if self.last_run is None:self.error(ValueError('Export this analysis first.'));return
        from microscopy.particle_review import prepare_review
        from manual_lengths import ManualLengthWindow
        try:
            model,image=prepare_review(Path(__file__).resolve().parent,self.last_run,'own_image')
            self.length_window=ManualLengthWindow(model,image);self.length_window.fig.canvas.manager.show()
        except (ValueError,OSError) as error:self.error(error)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path,help='Your TIFF. Omit it to choose a file in a window.')
    parser.add_argument('--inspect',action='store_true',help='List TIFF pages/series without analysing.')
    parser.add_argument('--page',type=int);parser.add_argument('--channel',type=int)
    parser.add_argument('--threshold',type=float,help='Threshold in native intensity units; supplying it runs noninteractively unless --gui is set.')
    parser.add_argument('--gui',action='store_true',help='Open the interactive preview even with a supplied threshold.')
    parser.add_argument('--crop',type=int,nargs=4,metavar=('R0','R1','C0','C1'))
    parser.add_argument('--polarity',choices=['dark','bright'],default='dark')
    parser.add_argument('--method',choices=['connected','watershed'],default='connected')
    parser.add_argument('--min-area',type=int,default=1)
    parser.add_argument('--nm-per-pixel',type=float,help='User-verified isotropic calibration; omitted means pixel units only.')
    parser.add_argument('--window-size',type=int,default=11)
    parser.add_argument('--min-peak-height',type=float,default=2)
    parser.add_argument('--min-seed-separation',type=float,default=5)
    parser.add_argument('--prominence',type=float,default=.25)
    parser.add_argument('--gaussian-sigma',type=float,default=0)
    parser.add_argument('--background-radius',type=int,default=0,help='Half-width of a square morphological background window; 0 = off.')
    parser.add_argument('--histogram-bins',type=int,default=12)
    parser.add_argument('--reference',type=Path,help='Optional aligned full-plane instance-label TIFF, background 0.')
    parser.add_argument('--link-fraction',type=float,default=.1)
    parser.add_argument('--min-match-iou',type=float,default=.5)
    args=parser.parse_args()
    interactive=args.gui or (args.threshold is None and not args.inspect)
    import matplotlib
    matplotlib.use('TkAgg' if interactive else 'Agg')
    if interactive:
        import tkinter as tk
        from tkinter import filedialog,messagebox
        root=tk.Tk();root.withdraw()
        path=args.image or filedialog.askopenfilename(parent=root,title='Choose your microscopy TIFF',filetypes=[('TIFF images','*.tif *.tiff'),('All files','*.*')])
        if not path:root.destroy();return
        try:OwnImageWindow(root,path,args)
        except (ValueError,OSError,ImportError) as error:messagebox.showerror('Cannot open TIFF',str(error),parent=root);root.destroy();return
        root.deiconify();root.mainloop();return
    if args.image is None:parser.error('--image PATH is required for noninteractive inspection or analysis.')
    from microscopy.user_images import inspect_tiff,load_tiff_plane,export_user_analysis
    try:
        if args.inspect:print(json.dumps(inspect_tiff(args.image),indent=2));return
        plane,selection=load_tiff_plane(args.image,args.page,args.channel)
        r0,r1,c0,c1=args.crop or [0,plane.shape[0],0,plane.shape[1]]
        settings=dict(crop_rows=[r0,r1],crop_columns=[c0,c1],threshold=args.threshold,polarity=args.polarity,
                      method=args.method,min_area=args.min_area,window_size=args.window_size,
                      min_peak_height=args.min_peak_height,min_seed_separation=args.min_seed_separation,prominence=args.prominence,
                      gaussian_sigma=args.gaussian_sigma,background_radius=args.background_radius,histogram_bins=args.histogram_bins,
                      link_fraction=args.link_fraction,min_match_iou=args.min_match_iou)
        run,summary=export_user_analysis(Path(__file__).resolve().parent,args.image,plane,selection,settings,args.nm_per_pixel,
                        'User-entered isotropic scale; not independently verified' if args.nm_per_pixel is not None else 'not provided',reference_path=args.reference)
        print('Report:',run/'report.html');print('Measurements:',run/'own_image/regions.csv')
        print('Predicted regions:',summary['predicted_regions'],'; validation:',summary['validation_status'])
        print('Review command:',f'review_particles.py --run results/{run.name} --dataset own_image')
    except (ValueError,OSError,ImportError) as error:parser.error(str(error))


if __name__=='__main__':main()
