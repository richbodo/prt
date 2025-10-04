import ollama

# This is our "Hello, World!" prompt for the model
prompt = "In one short sentence, what is a key feature of the Gemma model family?"

print(f"-> Asking VaultGemma: '{prompt}'")
print("-" * 20)

try:
    # Make the API call to the local Ollama server
    response = ollama.chat(
        model="vaultgemma",
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    # Extract and print the model's response
    answer = response["message"]["content"]
    print("<- VaultGemma's response:")
    print(answer)

except Exception as e:
    print(f"An error occurred: {e}")
    print("Is the Ollama application running?")
