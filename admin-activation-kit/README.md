# MagxxicVOT XII Admin Activation Kit

This kit is for administrators to generate activation tokens for users based on their Hardware ID (HWID).

### Instructions:
1. Ask the user for their HWID (displayed when they run the sender for the first time).
2. Run `generator.js` (Node.js) or `generator.py` (Python) and enter the user's HWID.
3. The generator will output an **Obfuscated Token**.
4. Send this obfuscated token to the user and tell them to save it in a file named `activation.sys` in the sender's root directory.
5. Alternatively, the user can manually enter the **Raw Token** when prompted by the sender.

### Files:
- `generator.js`: Node.js version of the activation generator.
- `generator.py`: Python version of the activation generator.
- `run_node.bat`: Run the Node.js generator (Windows).
- `run_python.bat`: Run the Python generator (Windows).
