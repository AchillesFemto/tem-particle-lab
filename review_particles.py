"""Review particle identities and outlines, then export versioned shape measurements."""
import argparse
from pathlib import Path
import numpy as np

class ReviewWindow:
    def __init__(self, model, image):
        import matplotlib.pyplot as plt
        from matplotlib.widgets import Button, TextBox
        self.plt=plt;self.model=model;self.image=image
        self.selected=[];self.selector=None;self.busy=False;self.message='Click a particle; cyan = predicted outline. Saved review statuses appear below.'
        self.fig=plt.figure(figsize=(14,9))
        self.overview=self.fig.add_axes([.035,.34,.45,.59])
        self.detail=self.fig.add_axes([.515,.34,.45,.59])
        self.info=self.fig.text(.04,.235,'',fontsize=10,va='top')
        self.status=self.fig.text(.04,.98,'',fontsize=11,va='top')
        note_ax=self.fig.add_axes([.15,.17,.80,.035]);self.note=TextBox(note_ax,'Reason: ')
        commands=[('Correct','correct'),('Split issue','split'),('Merge issue','merged'),('Uncertain','uncertain'),
                  ('Pending','pending'),('Next','next'),('Clear','clear'),('Merge selected','merge'),
                  ('Add polygon','add'),('Redraw boundary','replace'),('Draw split','split_region'),
                  ('Remove false +','remove'),('Undo','undo'),('Cancel drawing','cancel'),('Save version','save'),
                  ('Field inspected','inspect_field')]
        self.buttons=[]
        for i,(title,action) in enumerate(commands):
            row,col=divmod(i,8)
            ax=self.fig.add_axes([.025+col*.12,.105-row*.055,.115,.038])
            button=Button(ax,title);button.on_clicked(lambda event,a=action:self.action(a));self.buttons.append(button)
        self.fig.canvas.mpl_connect('button_press_event',self.click)
        self.fig.canvas.mpl_connect('close_event',self.close)
        self.redraw()

    def click(self,event):
        if self.busy or event.inaxes not in [self.overview,self.detail] or event.button!=1 or event.xdata is None:return
        row,column=int(round(event.ydata)),int(round(event.xdata))
        if not (0<=row<self.image.shape[0] and 0<=column<self.image.shape[1]):return
        label=int(self.model.labels[row,column])
        if label:
            if label in self.selected:self.selected.remove(label)
            else:self.selected.append(label)
            self.redraw()

    def redraw(self):
        from skimage.measure import regionprops,find_contours
        from microscopy.measurements import shape_measurements
        properties=regionprops(self.model.labels)
        for ax in [self.overview,self.detail]:
            ax.clear();ax.imshow(self.image,cmap='gray',vmin=0,vmax=255,interpolation='nearest')
            for p in properties:
                r0,c0,_,_=p.bbox
                color='yellow' if p.label in self.selected else 'cyan'
                for line in find_contours(np.pad(p.image,1),.5):
                    ax.plot(line[:,1]+c0-1,line[:,0]+r0-1,color=color,lw=.8)
                rr,cc=p.centroid;ax.text(cc,rr,str(p.label),color=color,fontsize=8,clip_on=True)
            ax.set_axis_off()
        self.overview.set_title('Whole crop: click labels to select / deselect')
        self.detail.set_title('Selected region: yellow outline; ellipse axes in red / blue')
        chosen=[p for p in properties if p.label in self.selected]
        if chosen:
            r0=min(p.bbox[0] for p in chosen);c0=min(p.bbox[1] for p in chosen)
            r1=max(p.bbox[2] for p in chosen);c1=max(p.bbox[3] for p in chosen)
            self.detail.set_xlim(max(-.5,c0-40),min(self.image.shape[1]-.5,c1+40))
            self.detail.set_ylim(min(self.image.shape[0]-.5,r1+40),max(-.5,r0-40))
        lines=[]
        for p in chosen[:2]:
            r,c=p.centroid;angle=p.orientation;m=shape_measurements(p,self.model.metadata['nm_per_pixel'])
            for length,dr,dc,color in [(p.axis_major_length,np.cos(angle),np.sin(angle),'red'),
                                       (p.axis_minor_length,-np.sin(angle),np.cos(angle),'deepskyblue')]:
                self.detail.plot([c-dc*length/2,c+dc*length/2],[r-dr*length/2,r+dr*length/2],color=color,lw=1.5)
            ratio='undefined' if m['ellipse_aspect_ratio'] is None else f"{m['ellipse_aspect_ratio']:.2f}"
            lines.append(f"Label {p.label}: {self.model.status[p.label]} | Feret max {m['feret_max_px']:.1f} px | ellipse major {m['ellipse_major_px']:.1f} px | minor {m['ellipse_minor_px']:.1f} px | aspect {ratio}")
        pending=sum(s=='pending' for s in self.model.status.values())
        lines.append(f'{len(properties)} regions; {pending} pending; whole-field inspection recorded: {self.model.field_inspected}. Human review is not independent ground truth.')
        self.info.set_text('\n'.join(lines));self.status.set_text(self.message[:160]);self.fig.canvas.draw_idle()

    def action(self,action):
        from matplotlib.widgets import PolygonSelector
        if self.busy and action!='cancel':return
        try:
            if action=='cancel':
                if self.selector:self.selector.disconnect_events();self.selector.set_visible(False)
                self.busy=False;self.message='Drawing cancelled; no pixels changed.'
            elif action=='clear':self.selected=[];self.message='Selection cleared.'
            elif action=='next':
                ids=sorted(self.model.status);current=max(self.selected,default=0)
                pending=[i for i in ids if self.model.status[i]=='pending']
                order=[i for i in pending if i>current]+[i for i in pending if i<=current]
                self.selected=order[:1];self.message='Next pending region selected.' if order else 'No pending regions; inspect the full field for missed particles.'
            elif action=='undo':self.model.undo();self.selected=[];self.message='Previous session edit reverted.'
            elif action=='inspect_field':
                if not self.note.text.strip():raise ValueError('Record how you checked the whole crop for missed objects.')
                self.model.inspect_field(self.note.text);self.message='Whole-field inspection recorded. Pending and uncertain regions still need review.'
            elif action=='save':
                out=self.model.save();self.message='Saved version: '+out.name;print('Saved review:',out,flush=True)
            elif action in ['add','replace','split_region']:
                if not self.note.text.strip():raise ValueError('Enter a reason before drawing a correction.')
                if action=='add' and self.selected:raise ValueError('Clear selection, then draw a missed particle.')
                if action!='add' and len(self.selected)!=1:raise ValueError('Select exactly one region first.')
                chosen=self.selected.copy();note=self.note.text
                self.busy=True;self.message='Draw on the RIGHT image; click the first vertex to finish. Cancel drawing abandons it.'
                self.selector=PolygonSelector(self.detail,lambda vertices:self.finish_polygon(action,chosen,note,vertices),useblit=True)
                self.status.set_text(self.message);self.fig.canvas.draw_idle();return
            else:
                self.model.apply(action,self.selected,note=self.note.text)
                self.selected=[i for i in self.selected if i in self.model.status]
                self.message='Recorded '+action+'. Edited regions return to pending; inspect before marking Correct.'
        except ValueError as error:self.message=str(error)
        self.redraw()

    def finish_polygon(self,action,selected,note,vertices):
        self.selector.disconnect_events();self.selector.set_visible(False);self.busy=False
        try:
            self.model.apply(action,selected,vertices,note);self.message='Correction applied. Review its boundary, then mark Correct.'
        except ValueError as error:self.message=str(error)
        self.redraw()

    def close(self,event):
        if self.model.log:
            out=self.model.save();print('Saved on close:',out,flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',help='Existing run path; default: newest compatible analysis run.')
    parser.add_argument('--dataset',help='Dataset ID; default: first successful development dataset, then another successful dataset.')
    parser.add_argument('--prepare',action='store_true',help='Save a pending review and preview; do not ask for human clicks.')
    args=parser.parse_args()
    from microscopy.run_selection import resolve_analysis
    project=Path(__file__).resolve().parent
    try:run,dataset=resolve_analysis(project,args.run,args.dataset)
    except ValueError as error:parser.error(str(error))
    print('Using run:',run,'; dataset:',dataset,flush=True)
    import matplotlib
    matplotlib.use('Agg' if args.prepare else 'TkAgg')
    from microscopy.particle_review import prepare_review
    model,image=prepare_review(project,run,dataset)
    window=ReviewWindow(model,image)
    if args.prepare:
        window.selected=sorted(model.status)[:1]
        window.redraw();model.folder.mkdir(parents=True,exist_ok=True)
        window.fig.savefig(model.folder/'review_preview.png',dpi=130)
        print('Prepared:',model.save(),'; no new human review recorded.',flush=True)
    else:window.plt.show()


if __name__=='__main__':main()
