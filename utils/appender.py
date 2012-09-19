import sys
annonce= sys.argv[1]

fil = open(annonce, "r")
content = fil.read()
fil.close()

if content.startswith("<?") :
    sys.exit(0)   

fil = open(annonce, "w")
fil.write('<?xml version="1.0" encoding="ISO-8859-1"?>\r\n<annonce>\r\n' + content + "\r\n</annonce>")
fil.close
