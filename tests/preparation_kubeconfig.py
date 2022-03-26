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
        "Config-Name": "minikube",
        "blacklist": ["default", "kube-public"],
        "concierge-endpoint": "https://161.35.248.164",
        "certificate-authority-data": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUJ4VENDQVd5Z0F3SUJBZ0lSQU5zTVdQQzlPRnN2bEx0QUNWUlp3eGN3Q2dZSUtvWkl6ajBFQXdJd01qRXcKTUM0R0ExVUVBeE1uVUdsdWJtbHdaV1FnU1cxd1pYSnpiMjVoZEdsdmJpQlFjbTk0ZVNCVFpYSjJhVzVuSUVOQgpNQ0FYRFRJeU1ESXlNakUwTXpRME1Gb1lEekl4TWpJd01USTVNVFF6T1RRd1dqQXlNVEF3TGdZRFZRUURFeWRRCmFXNXVhWEJsWkNCSmJYQmxjbk52Ym1GMGFXOXVJRkJ5YjNoNUlGTmxjblpwYm1jZ1EwRXdXVEFUQmdjcWhrak8KUFFJQkJnZ3Foa2pPUFFNQkJ3TkNBQVJQQ0FNclNiTGYveXVLc0g1azREdUp0SWNQUkhqdUNCQUJYT01UZ3R1ZApMZ1NScDdQb2UzY1VWMEZZTTVaU2RWamhDWkpLVHR3djlYLysrUHlIUmhMcm8yRXdYekFPQmdOVkhROEJBZjhFCkJBTUNBb1F3SFFZRFZSMGxCQll3RkFZSUt3WUJCUVVIQXdJR0NDc0dBUVVGQndNQk1BOEdBMVVkRXdFQi93UUYKTUFNQkFmOHdIUVlEVlIwT0JCWUVGRXR3L2tMalkrak8zWWdia2FTK3VSQldqd05PTUFvR0NDcUdTTTQ5QkFNQwpBMGNBTUVRQ0lBT0VhZGRxd3BBejZLVmI2bzZVREVQd2lhWnk2bm9uQm9oTWtDVndTazlrQWlBdTk2QjNCbU9uCkJoYU5NL29NUFBtMis5OTZiaFVQRUF3Z1VOcUZlMkVkK0E9PQotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg=="
    }
}"""

with open(store_path_kubedict, "w") as store_file:
    store_file.write(kubedict)