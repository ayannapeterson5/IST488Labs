import streamlit as st

choice = st.sidebar.selectbox(
    "Choose a lab",
    ["Lab 1", "Lab 2", "Lab 3", "Lab 4", "Lab 5", "Lab 6", "Lab 8"],
    index=6
)


if choice == "Lab 1":
    exec(open("Labs/Lab1.py").read())
elif choice == "Lab 2":
    exec(open("Labs/Lab2.py").read())
elif choice == "Lab 3":
    exec(open("Labs/Lab3.py").read())
elif choice == "Lab 4":
    exec(open("Labs/Lab4.py").read())
elif choice == "Lab 5":
    exec(open("Labs/Lab5.py").read())
elif choice == "Lab 6":
    exec(open("Labs/Lab6.py").read())
elif choice == "Lab 8":
    exec(open("Labs/Lab8.py").read())



