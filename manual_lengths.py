"""Record manual projected spans from two endpoints on the original selected plane."""
import argparse
import json
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4


class ManualLengthWindow:
    def __init__(self,model,image):
        import matplotlib.pyplot as plt
        from matplotlib.widgets import Button,TextBox,RadioButtons
        self.plt=plt;self.model=model;self.image=image;self.points=[];self.rows=[]
        from microscopy.measurements import measure_labels
        self.automatic={r['label']:r for r in measure_labels(model.labels,model.metadata['nm_per_pixel'])}
        self.fig,self.ax=plt.subplots(figsize=(9,8));self.fig.subplots_adjust(bottom=.27,right=.82)
        self.ax.imshow(image,cmap='gray',vmin=float(image.min()),vmax=float(image.max()),interpolation='nearest')
        self.ax.set_xlabel('Crop column (pixels)');self.ax.set_ylabel('Crop row (pixels)')
        self.ax.set_title('Click two endpoints on the same particle. Automatic outlines hidden.')
        self.line,=self.ax.plot([],[],color='orange',marker='x',lw=1.5)
        self.message=self.fig.text(.08,.20,'Projected straight-line span; not a curved centreline or guaranteed equivalent diameter.',fontsize=10)
        self.kind=RadioButtons(self.fig.add_axes([.84,.55,.15,.22]),['diameter','length','width'])
        self.identity=TextBox(self.fig.add_axes([.20,.13,.17,.035]),'Label (optional): ')
        self.note=TextBox(self.fig.add_axes([.48,.13,.40,.035]),'Note: ')
        self.buttons=[]
        for left,title,callback in [(.09,'Record span',self.record),(.32,'Clear points',self.clear),(.55,'Save version',self.save)]:
            button=Button(self.fig.add_axes([left,.055,.20,.045]),title);button.on_clicked(callback);self.buttons.append(button)
        self.fig.canvas.mpl_connect('button_press_event',self.click)
        self.fig.canvas.mpl_connect('close_event',self.close)

    def click(self,event):
        if event.inaxes!=self.ax or event.button!=1 or event.xdata is None:return
        if self.fig.canvas.toolbar and self.fig.canvas.toolbar.mode:return
        x,y=float(event.xdata),float(event.ydata)
        if not 0<=x<self.image.shape[1] or not 0<=y<self.image.shape[0]:return
        if len(self.points)==2:self.message.set_text('Record or clear the current pair before choosing another.');self.fig.canvas.draw_idle();return
        self.points.append((x,y));self.line.set_data([p[0] for p in self.points],[p[1] for p in self.points]);self.fig.canvas.draw_idle()

    def record(self,event=None):
        from microscopy.user_extensions import endpoint_measurement
        try:
            row=endpoint_measurement(self.points,self.model.metadata['nm_per_pixel'])
            identity=self.identity.text.strip();label=None if not identity else int(identity)
            if label is not None and label not in self.model.status:raise ValueError('Label is not present in this run/review.')
            for name in ['diameter_px','diameter_nm','feret_max_px','feret_max_nm','ellipse_major_px','ellipse_minor_px']:
                row['automatic_'+name]=self.automatic.get(label,{}).get(name)
            row['automatic_touches_crop_border']=self.automatic.get(label,{}).get('touches_crop_border')
            row['automatic_review_status']=self.model.status.get(label)
            row.update(kind=self.kind.value_selected,label=label,note=self.note.text,
                       source_row_1_px=row['row_1_px']+self.model.metadata['crop_rows'][0],
                       source_row_2_px=row['row_2_px']+self.model.metadata['crop_rows'][0],
                       source_column_1_px=row['column_1_px']+self.model.metadata['crop_columns'][0],
                       source_column_2_px=row['column_2_px']+self.model.metadata['crop_columns'][0])
            self.rows.append(row);self.points=[];self.line.set_data([],[])
            self.message.set_text(f"Recorded {row['kind']}: {row['span_px']:.2f} px; {len(self.rows)} manual span(s). Save periodically.")
        except ValueError as error:self.message.set_text(str(error))
        self.fig.canvas.draw_idle()

    def clear(self,event=None):
        self.points=[];self.line.set_data([],[]);self.message.set_text('Current endpoints cleared; recorded spans retained.');self.fig.canvas.draw_idle()

    def save(self,event=None,redraw=True):
        from microscopy.core import save_csv,save_json,fingerprint
        import hashlib
        if not self.rows:self.message.set_text('Record at least one endpoint pair first.');self.fig.canvas.draw_idle();return
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:6]
        folder=self.model.folder.parent/'manual_lengths'/stamp;folder.mkdir(parents=True)
        save_csv(folder/'manual_lengths.csv',self.rows,list(self.rows[0]))
        save_json(folder/'provenance.json',dict(source=self.model.metadata,
            displayed_label_map_sha256=hashlib.sha256(self.model.labels.tobytes()).hexdigest(),
            measurement_code_sha256=fingerprint(Path(__file__)),
            geometry_code_sha256=fingerprint(Path(__file__).resolve().parent/'microscopy/user_extensions.py'),
            recorded_spans=len(self.rows),automatic_outlines_displayed=False,
            caveat='Human endpoint choices are not absolute ground truth. Straight-line caliper spans and area-equivalent diameter/ellipse axes have different definitions; differences are not automatically errors. No diffusion, confidence interval or physical calibration is inferred.'))
        self.message.set_text('Saved manual spans: '+folder.name);print('Manual spans:',folder,flush=True)
        if redraw:self.fig.canvas.draw_idle()

    def close(self,event):
        if self.rows:self.save(redraw=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run');parser.add_argument('--dataset')
    args=parser.parse_args()
    import matplotlib
    matplotlib.use('TkAgg')
    from microscopy.run_selection import resolve_analysis
    from microscopy.particle_review import prepare_review
    project=Path(__file__).resolve().parent
    try:run,dataset=resolve_analysis(project,args.run,args.dataset);model,image=prepare_review(project,run,dataset)
    except (ValueError,OSError) as error:parser.error(str(error))
    print('Manual measurements use:',run,'dataset',dataset)
    window=ManualLengthWindow(model,image);window.plt.show()


if __name__=='__main__':main()
