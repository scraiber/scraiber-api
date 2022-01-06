import sys
import subprocess

kube_path = sys.argv[1]
store_path_kubeconfig = sys.argv[2]
store_path_kubedict = sys.argv[3]


file = open(kube_path, 'r')
file_lines = file.readlines()
 
with open(store_path_kubeconfig, "w") as store_file:
    for line in file_lines:
        if "certificate-authority:" in line:
            x = line.split("certificate-authority:")
            bas64_val = subprocess.check_output('cat '+x[1].replace("\n","")+' | base64 | tr -d "\n"', shell=True).decode('utf-8')
            store_file.write(x[0]+"certificate-authority-data: "+bas64_val+"\n")
            continue
        if "client-certificate:" in line:
            x = line.split("client-certificate:")
            bas64_val = subprocess.check_output('cat '+x[1].replace("\n","")+' | base64 | tr -d "\n"', shell=True).decode('utf-8')
            store_file.write(x[0]+"client-certificate-data: "+bas64_val+"\n")
            continue
        if "client-key:" in line:
            x = line.split("client-key:")
            bas64_val = subprocess.check_output('cat '+x[1].replace("\n","")+' | base64 | tr -d "\n"', shell=True).decode('utf-8')
            store_file.write(x[0]+"client-key-data: "+bas64_val+"\n")
            continue   
        store_file.write(line)


kubedict = """{ 
    "EU1": {
        "Location": "Frankfurt",
        "Config-Name": "minikube"
    }
}"""

with open(store_path_kubedict, "w") as store_file:
    store_file.write(kubedict)