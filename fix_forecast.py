import os

file_path = r'c:\Users\maram\Documents\vayuguard-aiml\website\forecast.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the last occurrence of the clean function
lines = content.split('\n')
keep = []
found_func = False
for line in lines:
    if 'async function triggerQuantumPrediction()' in line and not found_func:
        found_func = True
    if found_func:
        keep.append(line)
    # Stop after we have the function and closing tags
    if '</html>' in line and found_func:
        break

result = '\n'.join(keep)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(result)

print("Fixed! Kept only the clean triggerQuantumPrediction function and closing tags.")
print(f"Total lines kept: {len(keep)}")
