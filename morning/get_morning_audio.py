import os

# Define variables
url = "https://www.youtube.com/playlist?list=PLf4O_VcbYo27DpnCJZXRsxov6_DD2Q1NS"
output_folder = "audio"
download_video = False

exec(open("../common/get_video_audio.py").read())

# Find the first time when there's a blank line after a non-blank line in the description files, then keep only the lines before that
for root, dirs, files in os.walk(output_folder):
    for file in files:
        if file.endswith(".description"):
            description_path = os.path.join(root, file)
            with open(description_path, "r", encoding="utf-8") as f:
                content = f.readlines()
            for i in range(1, len(content)):
                if content[i - 1].strip() != "" and content[i].strip() == "":
                    with open(description_path, "w", encoding="utf-8") as f:
                        f.writelines(content[:i])
                    break
