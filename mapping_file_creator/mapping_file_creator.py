# =============================================================================
# Title:    Mapping File creator
# Version:  3.0
# Author:   Maartje Brouwer
# Goal:     Automating mapping file generation
# Date:     210322
# =============================================================================

## Uptil now we had to generate mapping files for every sequencing run by hand.
## Because we always make unique primer-pair combinations for every run, this
## needs to be done for every run seperately.
## In excel this is a lot of work, and often goes wrong. Therefore I would like
## to automate this process.

#### Import needed packages
import pandas as pd       # to be able to work with dataframes
from Bio.Seq import Seq   # to be able to do compl_rev


# !!! Set variables for your mappingfile
path = '//ZEUS/mmb/molecular_ecology/mollab_team/Sequencing/ngs_sequencing/210616_python_mapping_file_creator/'
file = path + 'test_template_for_mappingfile_creatorpy.csv'
NIOZnumber = 'testcsv_NIOZ313'
  # Sample_file must be .xlsx
  # Mapping file info must be 
  # $1 and $2 must be Forward_primer and Reverse_ primer
  # Primers should be written like: 515F_Golay001 / 926RBC_Golay252
  # You can add as many columns of metadata as you like
  # This metadata will be added to the end of the mappingfile
  # !!! The last column must be Description (sample name or control etc.)
  # Forward_primer;Reverse_primer;PurifMethod;TargetAmpliconSize;Description
  # 515F_Golay001;926RBC_Golay252;GelQuant;600bp400bp;1A1P
fw_primer = '515F'      # '515F' and '12S_F1a'are available
rv_primer = '926RBC'    # '806RB', '926RBC' and '12S_R1' are available
  # For any other primer we need to make a new .csv list
  # primer list must look like this: 3 columns:
  # $1 Forward_primer or Reverse_primer --> primername _Golay### 
  # $2 = ForwardPrimer or ReversePrimer --> primer sequence
  # $3 = LinkerPrimerSequence or Barcode_Reverse_Primer --> barcode sequence
  # i.e.: 
  # Reverse_primer;ReversePrimer;Barcode_Reverse_Primer
  # 926RBC_Golay002;CCGYCAATTYMTTTRAGTTT;CTTCCAACTCAT

  
# Import needed files
if file.endswith('.xlsx'):
    sample_file = pd.read_excel(file, sheet_name='FILL_IN')
if file.endswith('.csv'):
    sample_file = pd.read_csv(file, delimiter=';')

fw_primers = pd.read_csv(fw_primer + '.csv', delimiter=';')
rv_primers = pd.read_csv(rv_primer + '.csv', delimiter=';')

## Generate sampleIDs
# Create a new empty dataframe
df = pd.DataFrame()
# Insert primers
df['Forward_primer']=(sample_file['Forward_primer'])
df['Reverse_primer']=(sample_file['Reverse_primer'])
# Extract primernumbers
df['Forward_primer_number'] = (
    (sample_file['Forward_primer'].str.split('y',expand=True))[1].astype(str))
df['Reverse_primer_number'] = (
    (sample_file['Reverse_primer'].str.split('y',expand=True))[1].astype(str))
# Generate SampleIDs
df['#SampleID'] = (
    NIOZnumber + '.' + 
    df ['Forward_primer_number'] + '.' + 
    df ['Reverse_primer_number'])

## Add primer sequence and barcode sequences from database to samples
df = pd.merge(df, fw_primers)
df = pd.merge(df, rv_primers)

## Get complement reverse of reverse primer barcode
# Make empty new column
df ['RevComplReverseBarcodesequence'] = ''
# For every sample get the rev_compl of the reverse primer barcode
for sample in df.index:
    Barcode_Reverse_Primer = Seq(df['Barcode_Reverse_Primer'][sample])
    compl_rev_barcode = Barcode_Reverse_Primer.reverse_complement()
    # add reverse complement to the dataframe
    df.at[sample,'RevComplReverseBarcodesequence'] = compl_rev_barcode

## Construct BarcodeSequence (barcode_fwd + revcompl_barcode_rev)
# Make empty new column
df ['BarcodeSequence'] = ''
# For every sample make the BarcodeSequence
for sample in df.index:
    BarcodeSequence = ((df['Barcode_Forward_Primer'][sample]) + 
                        (df['RevComplReverseBarcodesequence'][sample]))
    # add BarcodeSequence to the dataframe
    df.at[sample,'BarcodeSequence'] = BarcodeSequence

## Assemble final mappingfile
# Make an empty dataframe
mf = pd.DataFrame()
# First column: SampleID
mf['#SampleID'] = df['#SampleID']
# Next column: BarcodeSequence
mf['BarcodeSequence'] = df['BarcodeSequence']
# Next column: LinkerPrimerSequence 
mf['LinkerPrimerSequence'] = df['LinkerPrimerSequence']
mf['ReversePrimerSequence'] = df['ReversePrimer']
# Next column: Forward and reverse barcode sequence
mf['Forward_barcode'] = df['Barcode_Forward_Primer']
mf['Reverse_barcode'] = df['Barcode_Reverse_Primer']
# Next columna: primer names
mf['ForwardPrimerName'] = df['Forward_primer']
mf['ReversePrimerName'] = df['Reverse_primer']


# After that... extra data from sample_file
for column in sample_file.columns[2:]:
    mf[column] = sample_file[column]
# Remove everything after the description column
mf = mf.loc[:,:'description']

## Save mapping_file
# Save file as RUNID_mapping_file.txt, tab delimited and without the index
mf.to_csv(path + NIOZnumber + "_mapping_file.txt", sep="\t", index=False)