

import socketscpi
ipAddress = '10.66.84.155'
instrument = socketscpi.SocketInstrument(ipAddress)
# instrument.write('*rst')
# print(
#     instrument.query('*opc?')
# )
try:
    instrument.err_check()
except socketscpi.SockInstError as e:
    print(str(e))
# print(instrument.query('SYSTem:COMMunicate:TCPip:CONTrol?'))
# print(instrument.query('MEASure[:SCALar]:CURRent[:DC]?'))
print(instrument.query('*OPS?'))
instrument.close()



# import pyvisa as visa
# rm = visa.ResourceManager('@py')
# print(rm.list_resources())
# inst = rm.open_resource('ASRL12::INSTR')
# print(inst.query("*IDN?"))


# import pyvisa as visa
#
# try:
#   resourceManager = visa.ResourceManager()
#   print(resourceManager.list_resources())
#   dev = 'TCPIP::K-B2901A-41308.local::5025::SOCKET'
#   session = resourceManager.open_resource(dev)
#   print('\n Open Successful!')
#   print('IDN:' +str(session.query('*IDN?')))
#
# except Exception as e:
#   print('[!] Exception:' +str(e))