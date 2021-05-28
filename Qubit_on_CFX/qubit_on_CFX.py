
# =============================================================================
# Title:    Qubit_on_CFX analysis tool
# Version:  1.0
# Author:   Maartje Brouwer
# Goal:     Automating qubit on CFX analysis
# Date:     210423
# =============================================================================

# !!! Make sure that your sample names start with HS_ or BR_
# !!! Make sure the standards are labelled 
# 'BR 0 ng', 'BR 200 ng', 'HS 0 ng' and 'HS 20 ng'

# !!! in CFX manager, save the data as excel
# in excel, save as .csv

# ==================Import needed packages=====================================
import pandas as pd, numpy as np
from natsort import index_natsorted 
 ## to be able to sort naturally, so 1,2,14,21 instead of 1,14,2,21
from scipy import stats
from matplotlib import pyplot as plt
# =============================================================================


# ==================Import file================================================
# =============================================================================
project = "210527-QubitLena"
csv = '210422-LenaQubit.csv'
data = pd.read_csv(csv, delimiter=';')
# =============================================================================


# ==================Making a standard curve====================================
# =============================================================================
# Extract standard curve data
stdcurveHSraw = data[(data["Sample"].str.startswith("HS "))]
stdcurveBRraw = data[(data["Sample"].str.startswith("BR "))]

# ==================High Sensitivity===========================================
# when there are HS measurements
if stdcurveHSraw.empty is False: 
    stdcurveHS = pd.DataFrame()
    # Cut ng/ul value from standard name
    stdcurveHS["ng/µl"] = (
        stdcurveHSraw["Sample"].str.split(' ', expand=True)[1].astype(float))
        # Expand, returns DataFrame instead of lists of strings
    # Get "End RFU" of the standards
    stdcurveHS["End RFU"] = stdcurveHSraw["End RFU"]
    # Linear regression + interpolation for standard curve
    HSslope, HSintercept, rv, pv, se = stats.linregress(stdcurveHS["ng/µl"], 
                                                        stdcurveHS["End RFU"])
    HS_interp = np.linspace(np.min(stdcurveHS["ng/µl"]), 
                            np.max(stdcurveHS["ng/µl"]), 
                            num=500)
    
# ==================Broad Range================================================
# when there are BR measurements
if stdcurveBRraw.empty is False: 
    # Make empty dataframe
    stdcurveBR = pd.DataFrame()
    # Cut ng/ul value from standard name
    stdcurveBR["ng/µl"] = (
        stdcurveBRraw["Sample"].str.split(' ', expand=True)[1].astype(float))
        # Expand, returns DataFrame instead of lists of strings
    # Get "End RFU" of the standards
    stdcurveBR["End RFU"] = stdcurveBRraw["End RFU"]

    # Linear regression + interpolation for standard curve
    BRslope, BRintercept, rv, pv, se = stats.linregress(stdcurveBR["ng/µl"], 
                         stdcurveBR["End RFU"])
    BR_interp = np.linspace(np.min(stdcurveBR["ng/µl"]), 
                    np.max(stdcurveBR["ng/µl"]), 
                    num=500)

# ==================Plot standard curves=======================================
# empty plot with 2 columns
fig, ax = plt.subplots(ncols=2, dpi=300)            

if stdcurveHSraw.empty is False:
    HSax = ax[0] # HS plot on the left
    HSax.set_xticks(np.arange(0,25,5)) # x-grid from 0 to 25, with intervals = 5
    HSax.grid(alpha=0.3) # transparancy of grid 
    HSax.set_title('standardcurve HS', fontsize=16)
    # plot HS curve
    HS = HSax.scatter(stdcurveHS["ng/µl"],      # x-axis
                      stdcurveHS["End RFU"],    # y-axis
                      c='lightsteelblue')       # color of the dots
    HSax.set_xlabel('DNA (ng/µl)')
    HSax.set_ylabel('end RFU')
    # draw standard curve line
    HSax.plot(
            HS_interp,                          # x-axis
            HSintercept + HSslope * HS_interp,  # y-axis
            linestyle='--',                     # style of the line
            c='cornflowerblue'                  # color of the line
            )
    # add equation to plot
    HSequation = (
        "y = " + str(round(HSslope)) + "X + " + str(round(HSintercept))
        )
    HSax.text(
        0.1, 0.9, HSequation, 
        size=8, color='purple', 
        transform=HSax.transAxes
        )

# plot BR curve
if stdcurveBRraw.empty is False:
    BRax = ax[1] # BR plot on the right
    BRax.set_xticks(np.arange(0,250,50)) # x-grid from 0 to 25, with intervals = 5
    BRax.grid(alpha=0.3)
    BRax.set_title('standardcurve BR', fontsize=16)
    BR = BRax.scatter(stdcurveBR["ng/µl"], 
                      stdcurveBR["End RFU"], 
                      c='cornflowerblue')
    BRax.set_xlabel('DNA (ng/µl)')
    BRax.set_ylabel('end RFU')
    # draw standard curve line
    BRax.plot(
            BR_interp,                          # x-axis
            BRintercept + BRslope * BR_interp,  # y-axis
            linestyle="--",                     # style of the line
            c='blue'                            # color of the line
            )
    # add equation to plot
    BRequation = (
        "y = " + str(round(BRslope)) + "X + " + str(round(BRintercept))
        )
    BRax.text(
        0.1, 0.9, BRequation, 
        size=8, color='purple', 
        transform=BRax.transAxes
        )
    
# make layout fit better
plt.tight_layout()
# save standard curve as .png
plt.savefig("output/standardcurve"+ project + ".png")
# =============================================================================

# ==================Calculating concentrations=================================
# =============================================================================
# Make new empty dataframes for HS and BR results
DNA_concentrations_HS = pd.DataFrame(columns = ["Sample"])
DNA_concentrations_BR = pd.DataFrame(columns = ["Sample"])

# ==================High Sensitivity===========================================
if stdcurveHSraw.empty is False:
    # Get data from HS samples only
    DNA_concentrations_HS_raw = data.loc[(data["Sample"].str.startswith("HS_"))]
    # Add HS sample names and RFU columns to results dataframe
    DNA_concentrations_HS["Sample"] = DNA_concentrations_HS_raw["Sample"]
    DNA_concentrations_HS["HS_RFU"] = DNA_concentrations_HS_raw["End RFU"]
    # Add a new column for the concentration
    DNA_concentrations_HS["HS_[DNA] ng/µL"] = ''
    # for every sample calculate concentration ((RFU - y-intercept) / slope)
    for sample in DNA_concentrations_HS.index:
        concentration = (
            ((DNA_concentrations_HS['HS_RFU'][sample]) - HSintercept) 
            / HSslope
            ) 
        # add concentration to the dataframe
        DNA_concentrations_HS.at[sample,'HS_[DNA] ng/µL'] = concentration
    # Get rid of HS in sample names, to be able to merge samples
    DNA_concentrations_HS['Sample'] = (
        (DNA_concentrations_HS['Sample'].str.split('_', 
        expand=True))[1].astype(str))

if stdcurveBRraw.empty is False:
    # Get data from BR samples only
    DNA_concentrations_BR_raw = data.loc[(data["Sample"].str.startswith("BR_"))]
    # Add BR sample names and RFU columns to results dataframe    
    DNA_concentrations_BR["Sample"] = DNA_concentrations_BR_raw["Sample"]
    DNA_concentrations_BR["BR_RFU"] = DNA_concentrations_BR_raw["End RFU"]
    # calculate concentration ((RFU - y-intercept) / slope)
    DNA_concentrations_BR["BR_[DNA] ng/µL"] = ''
    for sample in DNA_concentrations_BR.index:
        concentration = (
            ((DNA_concentrations_BR['BR_RFU'][sample]) - BRintercept) 
            / BRslope
            )
        # add concentration to the dataframe
        DNA_concentrations_BR.at[sample,'BR_[DNA] ng/µL'] = concentration

    # Get rid of BR in sample names, to be able to merge samples
    DNA_concentrations_BR['Sample'] = (
        (DNA_concentrations_BR['Sample'].str.split('_', 
        expand=True))[1].astype(str))

# Merge HS and BR measurements
DNA_concentrations = pd.merge(
    DNA_concentrations_HS, 
    DNA_concentrations_BR,
    how = 'outer',      # Use union of keys from both frames
    indicator = 'merge' # new column, that tells if both HS and BR are measured
    )
# Sort samples, naturally (so 1,2,14,21 instead of 1,14,2,21)
DNA_concentrations.sort_values(
    by=['Sample'], 
    inplace=True,
    key=lambda x: np.argsort(index_natsorted(DNA_concentrations["Sample"]))
    )

# Final column for concentration, chose if both are measured for BR or HS
DNA_concentrations['[DNA] ng/µL'] = ''
for index in DNA_concentrations.index:
    # If only HS is measured, concentration is HS measurement
    if DNA_concentrations.loc[index,'merge'] == 'left_only':
        DNA_concentrations.loc[index,'[DNA] ng/µL'] = DNA_concentrations.loc[index,'HS_[DNA] ng/µL']
    # If only BR is measured, concentration is BR measurement
    elif DNA_concentrations.loc[index,'merge'] == 'right_only':
        DNA_concentrations.loc[index,'[DNA] ng/µL'] = DNA_concentrations.loc[index,'BR_[DNA] ng/µL']
    # If both HS and BR is measured and BR[DNA] > 5 or HS[DNA] > 10,
    # concentration is BR measurement
    elif (DNA_concentrations.loc[index,'merge'] == 'both'
          and DNA_concentrations.loc[index,'BR_[DNA] ng/µL'] > 5
          or DNA_concentrations.loc[index,'HS_[DNA] ng/µL'] > 10
          ):
        DNA_concentrations.loc[index,'[DNA] ng/µL'] = DNA_concentrations.loc[index,'BR_[DNA] ng/µL']
    # If both HS and BR is measured and BR[DNA] <= 5,
    # concentration is HS measurement
    elif (DNA_concentrations.loc[index,'merge'] == 'both' 
          and DNA_concentrations.loc[index,'BR_[DNA] ng/µL'] <= 5
          ):
        DNA_concentrations.loc[index,'[DNA] ng/µL'] = DNA_concentrations.loc[index,'HS_[DNA] ng/µL']

# Remove the merge column
DNA_concentrations.drop(columns=['merge'], inplace=True)
         

# Save results in excel file
DNA_concentrations.to_excel('output/results' + project + '.xlsx', index=False)
    
# =============================================================================
                             