import os
import tkinter as tk
from lxml import etree as ET
from pathlib import Path

from tkinter import messagebox
from tkinter import filedialog
from tkinter import simpledialog
import tkinter.font as tkFont
import webbrowser

WINDOW_SIZE = 512
PARAM_WINDOW_X = 256
PARAM_WINDOW_Y = 780
GRID_BUTTON_SIZE_DIV = 5

# Variables
vertexShader = None
fragmentShader = None
paramsWindowOpen = False
parameters = [] # List of lists, index 0 is the name, index 1 is the type
windowsToDestroy = [] # Windows to destroy when the main window is closed
lastShaderName = "" # The last shader name that was used

lastParamsWindowX = 0
lastParamsWindowY = 0

# Main window
window = tk.Tk()
window.geometry(f"{WINDOW_SIZE}x{WINDOW_SIZE}")
window.resizable(False, False)
window.configure(background="#d1d1d1")
window.title("Repentance Shader to XML Converter")

def getFile(fileType, message):
    return filedialog.askopenfilename(filetypes=fileType, title=f"Select a {message} shader")

def storeVertexShader():
    global vertexShader
    vertexShader = getFile([("Vertex Shader", "*.glsl")], "vertex")

def storeFragmentShader():
    global fragmentShader
    fragmentShader = getFile([("Fragment Shader", "*.glsl")], "fragment")

def buildShader(root):
    shader = ET.SubElement(root, "shader")
    shader.set("name", lastShaderName)

    # Handle paramters (WIP)
    parameterElement = ET.SubElement(shader, "parameters")
    for paramaterData in parameters:
        param = ET.SubElement(parameterElement, "param")
        param.set("name", paramaterData[0].get())
        param.set("type", paramaterData[1].get())

    # Handle vertex shader
    vertexFile = open(vertexShader, "r")
    vertex = ET.SubElement(shader, "vertex")
    vertex.text = ET.CDATA("\n" + vertexFile.read() + "\n")

    vertexFile.close()

    # Handle fragment shader
    fragmentFile = open(fragmentShader, "r")
    fragment = ET.SubElement(shader, "fragment")
    fragment.text = ET.CDATA("\n" + fragmentFile.read() + "\n")

    fragmentFile.close()

def writeToFile():
    if vertexShader is None:
        messagebox.showerror("Error", "No vertex shader selected")
        return

    if fragmentShader is None:
        messagebox.showerror("Error", "No fragment shader selected")
        return

    if os.path.exists(vertexShader) is False:
        messagebox.showerror("Error", "Vertex shader file does not exist")
        return

    if os.path.exists(fragmentShader) is False:
        messagebox.showerror("Error", "Fragment shader file does not exist")
        return

    global lastShaderName
    answer = simpledialog.askstring("What is the name of your shader?", "Enter the name of your shader", initialvalue=lastShaderName, parent=window)
    if answer is None:
        return

    lastShaderName = answer

    saveFile = filedialog.asksaveasfilename(confirmoverwrite=True, defaultextension=".xml", filetypes=[("XML File", "*.xml")], title="Save XML File")

    # If the file exists, append to it
    if os.path.exists(saveFile) is True:
        parser = ET.XMLParser(strip_cdata=False)
        root = ET.parse(saveFile, parser).getroot()

        if root.tag != "shaders":
            messagebox.showerror("Error", "Invalid shaders.xml file")
            return

        # Check if the shader already exists
        for shader in root:
            if shader.get("name") == lastShaderName:
                # Overwrite the shader
                root.remove(shader)
                break

        buildShader(root)
    else:
        # Else, create a new file
        root = ET.Element("shaders")
        buildShader(root)

    # Write to the file
    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t", level=0)
    tree.write(saveFile)

def addParameterEntry(owner, button):
    parameters.append([tk.StringVar(), tk.StringVar()]) # Add a new parameter to the list
    slot = parameters.__len__() - 1
    parameters[slot][0].set(f"Parameter {slot + 1}")
    parameters[slot][1].set("float")
    addParameterFrame(owner, slot, button)

    if parameters.__len__() == 14:
        button.config(state="disabled")

def deleteParameterFrame(index, frame, paramAddButton):
    parameters.pop(index)
    paramAddButton.config(state="active")
    frame.destroy()

def addParameterFrame(owner, paramSlot, paramAddButton):
    backgroundColor = "#ededed"
    paramEntry = parameters[paramSlot]

    # odd entries are a different color
    if owner.winfo_children().__len__() % 2 + 1 == 0:
        backgroundColor = "#d6d6d6"

    param = tk.Frame(owner, padx=3, pady=5, background=backgroundColor, borderwidth=3, relief="sunken", border=3)
    param.pack_configure()

    # Name
    nameEntry = tk.Entry(param, borderwidth=3, relief="sunken", border=3, textvariable=paramEntry[0])
    nameEntry.pack_configure(anchor="w", side="left", fill="x", expand=True)

    # Type
    optionsList = ["float", "vec2", "vec3", "vec4"]
    typeDropdown = tk.OptionMenu(param, paramEntry[1], *optionsList)
    typeDropdown.pack_configure(anchor="center", side="left", fill="x", expand=True)

    # Delete button
    deleteButton = tk.Button(
        param,
        text="X",
        command= lambda : deleteParameterFrame(paramSlot, param, paramAddButton),
        relief="sunken",
        border=3,
        borderwidth=3,
        cursor="hand2",
        state="active",
    )
    deleteButton.pack_configure(anchor="e", side="left", fill="y", expand=True)

def toggleParamsWindowState(paramWindow):
    global paramsWindowOpen
    global lastParamsWindowX
    global lastParamsWindowY

    paramsWindowOpen = False
    windowsToDestroy.remove(paramWindow)
    lastParamsWindowX = paramWindow.winfo_x()
    lastParamsWindowY = paramWindow.winfo_y()
    paramWindow.destroy()

def closeMainWindow():
    for index in range(windowsToDestroy.__len__()):
        windowsToDestroy[index].destroy()
        windowsToDestroy.pop(index)

    window.destroy()

def parameterWindow():
    global paramsWindowOpen # i dont think i know how scope works
    global window
    if paramsWindowOpen is True:
        return

    paramWindow = tk.Toplevel()
    paramWindow.geometry(f"{PARAM_WINDOW_X}x{PARAM_WINDOW_Y}+{lastParamsWindowX}+{lastParamsWindowY}")
    paramWindow.resizable(False, False)
    paramWindow.title("Parameter Editor")
    paramWindow.protocol("WM_DELETE_WINDOW", lambda : toggleParamsWindowState(paramWindow))

    windowsToDestroy.append(paramWindow)
    paramsWindowOpen = True

    # Header
    textLabel = tk.Label(master=paramWindow, text="Add parameters (variables passed through Lua code) to your shader.", wraplength=PARAM_WINDOW_X - 20, font=("Arial", 14))
    textLabel.pack()

    # Param frame
    paramFrame = tk.Frame(master=paramWindow, padx=10, background="#adadad")

    # Param add button
    paramAddButton = tk.Button(
        master=paramWindow,
        text="Add parameter",
        command= lambda : addParameterEntry(paramFrame, paramAddButton),
    )
    paramAddButton.pack_configure(anchor="n", side="top", fill="x", pady=10)

    # Now add every button to the frame
    for i in range(parameters.__len__()):
        addParameterFrame(paramFrame, i, paramAddButton)

    # Pack the frame
    paramFrame.pack_configure(anchor="n", side="top", fill="both", expand=True)

def __main__():
    textLabel = tk.Label(text="Select a vertex and fragment shader. Make sure to add your parameters using the parameter editor.", wraplength=WINDOW_SIZE - 20, font=("Arial", 16), background="#d1d1d1")
    textLabel.pack()

    # Create the buttons
    # First create the frame that will hold the buttons in a grid
    buttonHolder = tk.Frame(master=window, height=WINDOW_SIZE - 12, width=WINDOW_SIZE, padx=20, background="#d1d1d1")
    buttonHolder.pack_configure(anchor="n", side="top", fill="both", expand=True)
    buttonHolder.grid_columnconfigure(0, weight=1)
    buttonHolder.grid_columnconfigure(1, weight=1)
    buttonHolder.grid_rowconfigure(0, weight=1)
    buttonHolder.grid_rowconfigure(1, weight=1)

    # Select the vertex shader
    vertexButton = tk.Button(
        master=buttonHolder,
        text="Select Vertex Shader File",
        command=lambda : storeVertexShader(),
        height=buttonHolder.winfo_height() // GRID_BUTTON_SIZE_DIV,
        width=buttonHolder.winfo_width() // GRID_BUTTON_SIZE_DIV,
        cursor="hand2"
    )
    vertexButton.grid(row=0, column=0, sticky="news", padx=7, pady=7)

    # Select the fragment shader
    fragmentButton = tk.Button(
        master=buttonHolder,
        text="Select Fragment Shader File",
        command=lambda : storeFragmentShader(),
        height=buttonHolder.winfo_height() // GRID_BUTTON_SIZE_DIV,
        width=buttonHolder.winfo_width() // GRID_BUTTON_SIZE_DIV,
        cursor="hand2"
    )
    fragmentButton.grid(row=0, column=1, sticky="news", padx=7, pady=7)

    # Create the parameter editor
    parameterEditor = tk.Button(
        master=buttonHolder,
        text="Parameter Editor",
        command=lambda : parameterWindow(),
        height=buttonHolder.winfo_height() // GRID_BUTTON_SIZE_DIV,
        width=buttonHolder.winfo_width() // GRID_BUTTON_SIZE_DIV,
        cursor="hand2"
    )
    parameterEditor.grid(row=1, column=0, sticky="news", padx=7, pady=7)

    # Create the convert button
    convertButton = tk.Button(
        master=buttonHolder,
        text="Convert",
        command=lambda : writeToFile(),
        height=buttonHolder.winfo_height() // GRID_BUTTON_SIZE_DIV,
        width=buttonHolder.winfo_width() // GRID_BUTTON_SIZE_DIV,
        cursor="hand2"
    )
    convertButton.grid(row=1, column=1, sticky="news", padx=7, pady=7)

    # Footer
    footerFont = tkFont.Font(family="Arial", size=12, underline=True, slant="italic")
    footer = tk.Label(text="Somewhat proudly made by catinsurance", justify="right", font=footerFont, anchor="e", padx=10, cursor="hand2", background="#d1d1d1")
    footer.bind("<ButtonRelease-1>", lambda _: webbrowser.open_new("https://github.com/maya-bee/shader-to-repentance/blob/main/LICENSE"))
    footer.pack_configure(side="right", fill="y", pady=3)

    window.protocol("WM_DELETE_WINDOW", lambda : closeMainWindow())
    window.mainloop()

    global lastParamsWindowX
    global lastParamsWindowY

    lastParamsWindowX = window.winfo_x()
    lastParamsWindowY = window.winfo_y()

__main__()