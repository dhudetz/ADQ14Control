import ctypes as ct
import sys
import os

# Define the record header struct
class HEADER(ct.Structure):
  _fields_ = [("RecordStatus", ct.c_ubyte),
              ("UserID", ct.c_ubyte),
              ("Channel", ct.c_ubyte),
              ("DataFormat", ct.c_ubyte),
              ("SerialNumber", ct.c_uint32),
              ("RecordNumber", ct.c_uint32),
              ("SamplePeriod", ct.c_int32),
              ("Timestamp", ct.c_int64),
              ("RecordStart", ct.c_int64),
              ("RecordLength", ct.c_uint32),
              ("Reserved", ct.c_uint32)]

# This function loads the ADQAPI library using ctypes
def adqapi_load(path='', quiet=False):
    if os.name == 'nt':
      if path == '':
        ADQAPI = ct.cdll.LoadLibrary('ADQAPI.dll')
      else:
        ADQAPI = ct.cdll.LoadLibrary(path)
    else:
      if path == '':
        ADQAPI = ct.cdll.LoadLibrary('libadq.so')
      else:
        ADQAPI = ct.cdll.LoadLibrary(path)

    # Manually set return type from some ADQAPI functions
    ADQAPI.CreateADQControlUnit.restype = ct.c_void_p
    ADQAPI.ADQ_GetRevision.restype = ct.c_void_p
    ADQAPI.ADQ_GetPtrStream.restype = ct.POINTER(ct.c_int16)
    ADQAPI.ADQControlUnit_FindDevices.argtypes = [ct.c_void_p]
    ADQAPI.ADQ_DebugCmd.argtypes = [ct.c_void_p, ct.c_void_p, ct.c_uint32,
                                    ct.c_uint32, ct.c_uint32, ct.c_uint32,
                                    ct.c_float, ct.c_void_p, ct.c_void_p,
                                    ct.c_void_p]
    ADQAPI.ADQ_GetBoardSerialNumber.restype = ct.c_char_p
    ADQAPI.ADQ_GetBoardProductName.restype = ct.c_char_p

    # Print ADQAPI revision
    if not quiet:
      print('ADQAPI loaded, revision {:d}.'.format(ADQAPI.ADQAPI_GetRevision()))

    return ADQAPI

# This function unloads the ADQAPI library using ctypes
def adqapi_unload(ADQAPI):
    if os.name == 'nt':
        # Unload DLL
        ct.windll.kernel32.FreeLibrary(ADQAPI._handle)

# Convenience function when printing status from ADQAPI functions
def adq_status(status):
  if (status==0):
    return 'FAILURE'
  else:
    return 'OK'

# Print revision info for an ADQ device
def print_adq_device_revisions(ADQAPI, adq_cu, adq_num):
    # Get revision info from ADQ
    rev = ADQAPI.ADQ_GetRevision(adq_cu, adq_num)
    revision = ct.cast(rev,ct.POINTER(ct.c_int))
    print('\nConnected to ADQ #{:d}'.format(adq_num))
    # Print revision information
    print('FPGA Revision: {}'.format(revision[0]))
    if (revision[1]):
        print('Local copy')
    else:
        print('SVN Managed')
        if (revision[2]):
            print('Mixed Revision')
        else :
            print('SVN Updated')
            print('')

# This function sets an alternating background color for a matplotlib plot
def alternate_background(ax, start_point, widths, labels=False,
                         color='#dddddd'):

    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import numpy as np
    ax.relim()
    # update ax.viewLim using the new dataLim
    ax.autoscale_view()
    plt.draw()

    # Calculate starting points
    edges = start_point+np.cumsum(np.append([0],widths))
    # Set plot x axis length
    ax.set_xlim(start_point, edges[-1])
    ylim=ax.get_ylim()
    # Draw colored fields for every other width
    for idx in range(1,len(edges)-1,2):
        ax.add_patch(
            patches.Rectangle(
                (edges[idx], ylim[0]), # point(x,y)
                widths[idx], # width
                ylim[1]-ylim[0], # height
                facecolor=color,
                edgecolor='none',
                zorder=-20
                )
            )
    # Optionally draw labels
    if labels==True:
        for idx in range(0,len(edges)-1):
            # Set y-position 1% under top
            ypos=(ylim[1])-0.01*(ylim[1]-ylim[0])
            # Enumerate fields
            plt.text(edges[idx], ypos,
                     'R{}'.format(idx), verticalalignment='top')
