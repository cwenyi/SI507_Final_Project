enter = input("Please choose Movie or Drama: ")

if enter.lower() == 'drama':
    import drama 
elif enter.lower() == 'movie':
    import movie 
else:
    print("Invalid option")


