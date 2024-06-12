import streamlit.components.v1 as components

def set_email_to_session_storage(email: str):
    js_code = f"""
    <script>
    sessionStorage.setItem('email', '{email}');
    </script>
    """
    components.html(js_code)

def get_email_from_session_storage():
    js_code = """
    <script>
    const email = sessionStorage.getItem('email') || '';
    return email;
    </script>
    """
    return components.html(js_code, height=0)

