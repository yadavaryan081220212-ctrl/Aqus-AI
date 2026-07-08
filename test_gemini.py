import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import google.generativeai as genai

genai.configure(api_key="AIzaSyAMW9hlhAFYANUjKXM8LGHAblP1LFWpZ1Q")

print("Listing models:")
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(f"- {m.name}")
