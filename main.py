# Read the input string from the command line
input_string = input("Enter a string: ")

# Initialize counters for the number of vowels and consonants
num_vowels = 0
num_consonants = 0

# Iterate through the input string and count the number of vowels and consonants
for ch in input_string:
    ch = ch.lower()
    if ch in "aeiou":
        num_vowels += 1
    elif ch.isalpha():
        num_consonants += 1

# Print the results
print("Number of vowels:", num_vowels)
print("Number of consonants:", num_consonants)