"""Run the static-image and/or movie workflow."""
import argparse
import importlib
import os
import warnings


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=["static","dynamics","all"],nargs="?",default="all")
    parser.add_argument("--show",action="store_true",help="Open interactive plots.")
    args=parser.parse_args()
    if not args.show: os.environ["MPLBACKEND"]="Agg"
    stages={"static":[24,25,26,27],"dynamics":[28],"all":[24,25,26,27,28]}[args.mode]
    import matplotlib.pyplot as plt
    for number in stages:
        print(f"Running lesson {number}...",flush=True)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore",message="FigureCanvasAgg is non-interactive.*")
            importlib.import_module(f"lesson_{number:02d}").main()
        plt.close("all")
    print("Workflow complete. Inspect saved figures, parameters and diagnostic tables.")


if __name__=="__main__": main()
