import numpy as np
import matplotlib.pyplot as plt

file = open("statistics.txt", mode="r")
Lines = file.readlines()
distance1 = np.linspace(0, 5, 10)
data1 =np.array([0.7  , 0.75 , 0.65 , 0.645, 0.585, 0.62 , 0.53 , 0.56 , 0.51 ,0.525]) # this is average fid from basic test 
data2 = [0.82,  0.835, 0.73,  0.74,  0.675, 0.7,   0.675, 0.74,  0.63,  0.615] # triangle
data3 = [0.92,  0.93,  0.84,  0.88,  0.82,  0.78,  0.755, 0.805, 0.73,  0.705]

distance = [distance1,distance1,distance1]
data = [data1,data2,data3]

my_data = np.loadtxt('statistics.txt',comments='runs',delimiter=',')

average_fidelity = my_data[:,1]
print(average_fidelity)

plt.figure(figsize=(8.5,8.5))
plt.tick_params(axis='both', which='major', labelsize=10)
plt.tick_params(axis='both', which='minor', labelsize=10)
plt.xlabel("Network channel length (Km)", fontsize=10)
plt.ylabel("Average entanglement efficiency rate ", fontsize=10)
col = ['k','b','r']
label = ['Butterfly Model','Triangle Model','Twin Model']#,'2','3']#,'44']
for i in range(3):
    plt.plot(distance[i],data[i],markersize= 10,color=col[i],marker='d', label=str(label[i]))

plt.legend(loc='upper right')
#plt.show()
plt.savefig('mulitpartite-size.png')
# label = ['1']#,'2','3']#,'44']
# upper_lim = max(optimal_ls[2])+0.5
# plt.figure(figsize=(8.5,8.5))
# #plt.suptitle('Sum Rate 3-3 ',fontsize=30)
# plt.tick_params(axis='both', which='major', labelsize=20)
# plt.tick_params(axis='both', which='minor', labelsize=20)
# plt.xlabel("Power Contraint (dB)", fontsize=30)
# plt.ylabel("Average sum rate bit/ (dB)", fontsize=30)
# plt.ylim(0,upper_lim+0.5)
# plt.xlim(0,np.max(PR_dB))
# col = ['k','b','r']
# for i in range(3):
#     #plt.grid(color='k', linestyle='-',alpha=0.5, linewidth=0.5)
#     plt.plot(PR_dB,optimal_ls[i],markersize= 10,color=col[i],marker='d', label='Optimal '+str(label[i]))
#     plt.plot(PR_dB,scaled_ls[i],markersize= 10,color=col[i],marker='s',label='Scaled ouput '+str(label[i]))
#     plt.plot(PR_dB,actual_ls[i],markersize= 10,color=col[i],marker='o',label='Learnt output '+str(label[i]))
# plt.legend(loc='upper left')
# plt.show()