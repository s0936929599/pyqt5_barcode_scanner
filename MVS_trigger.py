import clr
import ctypes
clr.FindAssembly('AXMVS100_dotNet.dll')
clr.AddReference('AXMVS100_dotNet')
import AXMVS100_dotNet
import time

def main():
	device_ = AXMVS100_dotNet.AXMVS100();

	result = device_.AXMVS100_TriggerIn_SetConfig(0,3)
	#print(f'AXMVS100_TriggerIn_SetConfig:{result}')
	result = device_.AXMVS100_TriggerOut_SetConfig(0,0,0,0,0,1,0)
	#print(f'AXMVS100_TriggerOut_SetConfig:{result}')
	result = device_.AXMVS100_TriggerOut_SetSignal(0,0,1000)
	#print(f'AXMVS100_TriggerOut_SetSignal:{result}')
	result = device_.AXMVS100_TriggerOut_Enable(1) #0x00000001、#0x00000011
	#print(f'AXMVS100_TriggerOut_Enable:{result}')

	result = device_.AXMVS100_LightingCtrl_SetConfig(1,0,0,0,1,0,0,0)
	#print(f'AXMVS100_LightingCtrl_SetConfig:{result}')
	result = device_.AXMVS100_LightingCtrl_SetSignal(1,0,100,5)
	#print(f'AXMVS100_LightingCtrl_SetSignal:{result}')
	result = device_.AXMVS100_LightingCtrl_Enable(1)
	#print(f'AXMVS100_LightingCtrl_Enable:{result}')

if __name__=='__main__':
	main()
