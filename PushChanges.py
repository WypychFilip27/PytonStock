import os
from datetime import datetime

print("Backup preparing...")
print("git config user.email")
os.system("git config user.email")

# Calling system commands
os.system("git add .")
data = datetime.now().strftime("%Y-%m-%d %H:%M")
os.system(f'git commit -m "Changes: {data}"')
os.system("git push")

print("Sent to github!")