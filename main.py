import streamlit as st
import requests
import json

# --- Piston API Configuration ---
PISTON_URL = "https://emkc.org/api/v2/piston/execute"
SUPPORTED_LANGUAGES = {
    "python": ["py", "python3"],
    "javascript": ["js", "node"],
    "java": ["java"],
    "c": ["c"],
    "cpp": ["cpp", "c++"],
    "go": ["go", "golang"],
    "rust": ["rs", "rust"],
    "bash": ["sh", "bash"],
}
LANGUAGE_OPTIONS = list(SUPPORTED_LANGUAGES.keys())

# --- Example Code Snippets (Optional Enhancement) ---
EXAMPLE_CODE = {
    "python": "def greet(name):\n  print(f\"Hello, {name}!\")\n\ngreet(\"Streamlit\")",
    "javascript": "function greet(name) {\n  console.log(`Hello, ${name}!`);\n}\n\ngreet(\"Streamlit\");",
    "java": """
public class HelloWorld {
    public static void main(String[] args) {
        String name = "Streamlit";
        System.out.println("Hello, " + name + "!");
    }
}
""",
    "c": """
#include <stdio.h>

int main() {
   char name[] = "Streamlit";
   printf("Hello, %s!\\n", name);
   return 0;
}
""",
   "cpp": """
#include <iostream>
#include <string>

int main() {
    std::string name = "Streamlit";
    std::cout << "Hello, " << name << "!" << std::endl;
    return 0;
}
""",
    "go": """
package main

import "fmt"

func main() {
    name := "Streamlit"
    fmt.Printf("Hello, %s!\\n", name)
}
""",
   "rust": """
fn main() {
    let name = "Streamlit";
    println!("Hello, {}!", name);
}
""",
    "bash": "name=\"Streamlit\"\necho \"Hello, $name!\""
}

# --- Backend Function (Unchanged from Streamlit version) ---
def debug_code(language, version, code):
    """Sends code to the Piston API."""
    piston_lang = language
    payload = { "language": piston_lang, "version": version, "files": [{"content": code}],
                "stdin": "", "args": [], "compile_timeout": 10000, "run_timeout": 3000,
                "compile_memory_limit": -1, "run_memory_limit": -1 }
    try:
        response = requests.post(PISTON_URL, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("❌ Error: The request to the Piston API timed out.")
        return None
    except requests.exceptions.RequestException as e:
        error_message = f"❌ Error communicating with the Piston API: {e}"
        try:
            error_details = e.response.json()
            if 'message' in error_details: error_message += f"\nAPI Message: {error_details['message']}"
        except: pass
        st.error(error_message)
        return None
    except Exception as e:
        st.error(f"❌ An unexpected error occurred: {e}")
        return None

# --- Initialize Session State ---
if 'code_input' not in st.session_state:
    st.session_state.code_input = "" # Store code input here
if 'last_debug_result' not in st.session_state:
    st.session_state.last_debug_result = None # Store the result dict
if 'last_language' not in st.session_state:
     st.session_state.last_language = LANGUAGE_OPTIONS[0]

# --- Streamlit UI Definition ---
st.set_page_config(page_title="Code Debugger", layout="wide", initial_sidebar_state="collapsed")

st.title("🤖 Code Debugging Assistant")
st.caption("Execute code snippets quickly using the Piston API")

# Use columns for layout
col1, col2 = st.columns([2, 3]) # Give output slightly more space

with col1:
    st.header("📝 Input")

    # Language Selection
    selected_language = st.selectbox(
        "Select Language:",
        options=LANGUAGE_OPTIONS,
        index=LANGUAGE_OPTIONS.index(st.session_state.last_language), # Remember last selection
        key='selected_language_key', # Give it a key for potential future use
        help="Choose the programming language of your code snippet."
    )
    # Update session state if language changes
    st.session_state.last_language = selected_language


    # Code Input Area - Use session state to control its value
    st.session_state.code_input = st.text_area(
        f"Enter your {selected_language} code here:",
        value=st.session_state.code_input, # Controlled component
        height=300,
        key='code_input_area', # Assign a key for the clear function
        placeholder=f"Paste or type your {selected_language} code here...",
        help="Type your code snippet. The API will execute this code."
    )

    # --- Buttons Row ---
    button_col1, button_col2, button_col3 = st.columns([1,1,1])

    with button_col1:
        debug_button = st.button("▶️ Debug Code", type="primary", use_container_width=True)

    with button_col2:
        clear_button = st.button("🗑️ Clear All", use_container_width=True)

    with button_col3:
        example_button = st.button("💡 Load Example", use_container_width=True)


    # --- Button Logic ---
    if clear_button:
        st.session_state.code_input = "" # Clear code in state
        st.session_state.last_debug_result = None # Clear results in state
        # The text_area will automatically update because its value is bound to st.session_state.code_input
        # We need to trigger a rerun to clear the output area if needed, Streamlit does this automatically on button click.

    if example_button:
         st.session_state.code_input = EXAMPLE_CODE.get(selected_language, "# No example available for this language.")
         st.session_state.last_debug_result = None # Clear previous results when loading example
         # Rerun happens automatically

    if debug_button:
        code_to_run = st.session_state.code_input # Get code from state
        if not code_to_run.strip():
             st.toast("⚠️ Please enter some code to debug.", icon="⚠️") # Use toast for transient warnings
        else:
            # Show a spinner while processing
            with st.spinner(f"⚙️ Running {selected_language} code..."):
                # Call the backend function using code from session state
                response = debug_code(selected_language, "*", code_to_run)
                # Store the result in session state to display it
                st.session_state.last_debug_result = response
                st.session_state.last_language_run = selected_language # Remember which lang was run
            # Rerun happens automatically after button logic finishes


# --- Output Display Area ---
with col2:
    st.header("📊 Output")

    # Display results stored in session state
    result = st.session_state.last_debug_result
    lang_run = st.session_state.get('last_language_run', None) # Get the language that produced this result

    if result is None:
        st.info("Enter code and click 'Debug Code' to see the results here.")
    else:
        # Determine overall status
        compile_ok = result.get('compile', {}).get('code', 0) == 0
        run_ok = result.get('run', {}).get('code', 0) == 0
        overall_success = compile_ok and run_ok

        if overall_success:
            st.success("✅ Execution Completed Successfully!")
        else:
            st.error("❌ Execution Finished with Errors.")

        # --- Compilation Stage Expander ---
        compile_output = result.get('compile', {})
        has_compile_output = compile_output and (compile_output.get('stdout') or compile_output.get('stderr'))
        if has_compile_output:
             # Expand compilation details only if there was output or an error
             expand_compile = not compile_ok or bool(compile_output.get('stdout'))
             with st.expander("Compilation Stage Details", expanded=expand_compile):
                 if compile_output.get('stdout'):
                     st.text("Compiler Output (stdout):")
                     st.code(compile_output['stdout'], language=lang_run)
                 if compile_output.get('stderr'):
                     st.warning("Compiler Errors/Warnings (stderr):") # Use warning for stderr
                     st.code(compile_output['stderr'], language=lang_run)
                 compile_exit_code = compile_output.get('code')
                 if compile_exit_code == 0:
                      st.caption(f"Compile Exit Code: {compile_exit_code}")
                 else:
                      st.warning(f"Compile Exit Code: {compile_exit_code}")


        # --- Runtime Stage Expander ---
        run_output = result.get('run', {})
        has_run_output = run_output and (run_output.get('stdout') or run_output.get('stderr'))
        if has_run_output:
            # Expand runtime details if there was output or an error
            expand_run = not run_ok or bool(run_output.get('stdout'))
            with st.expander("Runtime Stage Details", expanded=expand_run):
                if run_output.get('stdout'):
                    st.text("Program Output (stdout):")
                    st.code(run_output['stdout'], language=lang_run)
                if run_output.get('stderr'):
                    st.error("Runtime Error Output (stderr):") # Use error for runtime stderr
                    st.code(run_output['stderr'], language=lang_run)
                run_exit_code = run_output.get('code')
                if run_exit_code == 0:
                     st.caption(f"Runtime Exit Code: {run_exit_code}")
                else:
                     st.error(f"Runtime Exit Code: {run_exit_code}")

        elif not has_compile_output:
             st.info("No output (stdout/stderr) was produced during compilation or runtime.")

# Optional: Add footer
st.markdown("---")
st.caption("Built with Streamlit | Code execution via Piston API")