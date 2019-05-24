file = open("./CarNN-6-2-8-2.model", "r") 
weights = file.read().split(" ")[4:]
print("""float weights[] = {
    """+", ".join(weights)+"""
};""")