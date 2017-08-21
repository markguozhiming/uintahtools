"""Simple plotting script for Plotting Udas from UPSes.

Provide the x variable and the y variable to be plotted along with the uda-folder
to make a simple 2D scatter plot with matplotlib. Output points are also stored in 
a dat-file.

"""
import os
import re
from functools import partial
import numpy as np
from pandas import Series, DataFrame
import pandas as pd
import subprocess
from pathlib import Path
from ruamel.yaml import YAML
from uintahtools import CONFIG

# Creating global variable PUDA
yaml = YAML()
load = yaml.load(Path(CONFIG))
PUDA = "/".join([os.path.dirname(load['uintahpath']), "puda"])

def header(var):
    """Creates column headers based on extracted variable."""
    FIXEDCOLS = ["time", "patch", "matl", "partId"]
    HEADERS = {
        "p.x": ["x", "y", "z"],
        "p.porepressure": ["pw"],
    }
    if var not in HEADERS:
        print("Sorry, the variable {var} is not implemented yet. No headers assigned for {var}".format(var=var))
        return FIXEDCOLS + [var]
    return FIXEDCOLS + HEADERS[var]

def normalize(var, varmax, varmin=0, flip=False):
    """Function to normalize var with regards to wrt.
    
    Normalizes to the range [0, 1] where var_min scales to 0 by default,
    and the range can be flipped. Resulting values can lie outside the range.

    """
    return (varmax - var)/(varmax-varmin) if flip else (var-varmin)/(varmax-varmin)

def get_timestep(time, uda):
    """For a given time, return the timestep number.
    
    Uintah timesteps equals rounded off time*1e5. Will return
    the closest timestep by default if input time is between valid timesteps.

    """
    conversion_factor = 1e5
    # Convert time to timestep:
    timestep = int(time*conversion_factor)

    cmd = [PUDA, "-timesteps", uda]
    # Running the command, fetching the output and decode it to string
    result = re.findall(
        "(?P<timestep>\d+): .*",
        subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode("utf-8"),
        re.MULTILINE)
    
    # Check if timestep is within bounds:
    maxstep = int(result[-1])
    if timestep > maxstep:
        raise AttributeError(
            "Provided time {time} is out of bounds. Max time is {max}".format(
                time=time,
                max=maxstep/conversion_factor
            ))

    return str(timestep) if timestep in result else \
            min(result, key=lambda k: abs(int(k)-timestep))

def construct_cmd(var, uda, time=None):
    """Creating the command line instruction to extract variable.
    
    If time is provided, the timestep options are included in the command.
    """
#  ~/trunk/dbg/StandAlone/puda -partvar $1 ~/trunk/tests/1Dworking.uda >> $2
    cmd = [PUDA, "-partvar", var, uda]
    if time:
        if isinstance(time, list):
            cmd[-1:-1] = ["-timesteplow", str(time[0]), "-timestephigh", str(time[1])]
        else:
            cmd[-1:-1] = ["-timesteplow", str(time), "-timestephigh", str(time)]
    return cmd

def udaplot(x, y, uda):
    """Main function.

    Steps:
        1. Extract XVAR from uda <-|
        2. Extract YVAR from uda <-|-Both should pipe the output to the read_table function
      x 3. Store XVAR and YVAR in their respective dataframes
      x 4. Set column names
      x 5. Merge dataframes
      x 6. Drop duplicates (removes the need for line select)
      x 7. Column select: time, XVAR, YVAR
      x 8. Normalize variables
    """
    print("Plotting x:", x, " vs  y:", y, " contained in ", uda)
    
    # Extracting columns
    # subprocess.call(["./uintahtools/terzaghi", x, y])
    # print("Done with bashing about")
    read_table = partial(pd.read_table, header=None,
                                        skiprows=2,
                                        # nrows=100, #Uncomment for testing purposes
                                        sep="\s+"
                                        )

    timeseries = [0.02, 0.05, 0.1, 0.2, 0.5, 1]
    [print(construct_cmd("p.x", uda, time=time)) for time in timeseries]
    
    subprocess.call(construct_cmd("p.x", uda, time=[0.02, 1.1]))
    # df1 = read_table("ys.dat", names=header(y))
    # df2 = read_table("xs.dat", names=header(x))
    
    # selected = ['time', 'y', 'pw']
    
    # df = pd.merge(df1, df2).filter(selected).drop_duplicates(selected)
    
    # pwnorm = partial(normalize, varmax=-10000)
    # ynorm = partial(normalize, varmax=1, flip=True)
    
    # df['pw'] = df['pw'].map(lambda x: pwnorm(x))
    # df['y'] = df['y'].map(lambda x: ynorm(x))
    
    # print(df)