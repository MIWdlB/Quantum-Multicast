import numpy as np
import matplotlib.pyplot as plt

file = open("statistics.txt", mode="r")
Lines = file.readlines()
distance1 = np.linspace(0, 5, 10)
data1 =[0.7  , 0.75 , 0.65 , 0.645, 0.585, 0.62 , 0.53 , 0.56 , 0.51 ,0.525] # this is average fid from basic test 
data2 = [0.97916667, 1., 1., 1.,0.95652174, 1. ,1.,0.92857143, 1., 1.] # bipartite
data3=[]

distance = [distance1,distance1,distance1]
data = [data1,data2,data3]

# my_data = np.loadtxt('statistics.txt',comments='runs',delimiter=',')

# average_fidelity = my_data[:,1]
# print(average_fidelity)

plt.figure(figsize=(8.5,8.5))
plt.tick_params(axis='both', which='major', labelsize=10)
plt.tick_params(axis='both', which='minor', labelsize=10)
plt.xlabel("Network channel length (Km)", fontsize=10)
plt.ylabel("Average entanglement efficiency rate ", fontsize=10)
col = ['k','b','r']
label = ['Multipartite','Bipartite']#,'Twin Model']#,'2','3']#,'44']
for i in range(2):
    plt.plot(distance[i],data[i],markersize= 10,color=col[i],marker='d', label=str(label[i]))

plt.legend(loc='center right')
#plt.show()


plt.savefig('comparision.png')