"""Selection must work without a contributor's local run folders."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from microscopy.run_selection import resolve_analysis


class RunSelectionChecks(unittest.TestCase):
    def make_run(self,root,name,entries,complete_ids,timestamp):
        run=root/'results'/name;run.mkdir(parents=True)
        snapshot=run/'config_snapshot.json';snapshot.write_text(json.dumps({'datasets':entries}))
        os.utime(snapshot,(timestamp,timestamp))
        for identity in complete_ids:
            folder=run/identity;folder.mkdir()
            for filename in ['arrays.npz','summary.json','overlap_links.csv']:(folder/filename).touch()
        return run

    def test_fresh_checkout_has_actionable_message(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError,'Generate a run first'):
                resolve_analysis(Path(folder))

    def test_newest_complete_run_and_development_preference(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            entries=[{'id':'hold','role':'held_out_image'},{'id':'dev','role':'development'}]
            self.make_run(root,'older',entries,['dev'],100)
            newest=self.make_run(root,'newest',entries,['hold','dev'],200)
            self.make_run(root,'unfinished',entries,[],300)
            self.assertEqual(resolve_analysis(root),(newest,'dev'))
            self.assertEqual(resolve_analysis(root,dataset='hold'),(newest,'hold'))

    def test_explicit_relative_absolute_and_bad_dataset(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);run=self.make_run(root,'chosen',[{'id':'dev','role':'development'}],['dev'],100)
            self.assertEqual(resolve_analysis(root,'results/chosen','dev'),(run,'dev'))
            self.assertEqual(resolve_analysis(root,str(run),'dev'),(run,'dev'))
            with self.assertRaisesRegex(ValueError,'Configured IDs: dev'):
                resolve_analysis(root,'results/chosen','missing')

    def test_malformed_newest_skipped_and_failed_development_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            entries=[{'id':'dev','role':'development'},{'id':'hold','role':'held_out_image'}]
            run=self.make_run(root,'valid',entries,['hold'],100)
            bad=self.make_run(root,'broken',entries,[],200)
            (bad/'config_snapshot.json').write_text('invalid JSON')
            self.assertEqual(resolve_analysis(root),(run,'hold'))
            with self.assertRaisesRegex(ValueError,'Cannot read analysis run'):
                resolve_analysis(root,'results/broken')


if __name__=='__main__':unittest.main()
