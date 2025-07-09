// Script to auto toggle dark mode
function toggleDarkMode() {
    const currentHour = new Date().getHours();
    const isDayTime = currentHour >= 8 && currentHour < 18;
    document.body.classList.toggle('dark-mode', !isDayTime);
}
// Call the function initially
toggleDarkMode();
// Check every 10 minutes
setInterval(toggleDarkMode, 10 * 60 * 1000);

// script to copy code to user's clipboard on click
function copyToClipboard(codeId) {
    let text = ""
    const codeElement = document.getElementById(codeId);
    if (!codeElement) return;

    let childNodes = codeElement.childNodes;
    if (childNodes.length > 1) {
        text = childNodes[1].textContent.trim()
    } else {
        text = codeElement.innerText.trim();
    }
    // copy the text to clipboard
    navigator.clipboard.writeText(text).then(() => {
        // update copy icon style on copy
        const copyIcon = codeElement.parentElement.nextElementSibling;
        if (copyIcon) {
            copyIcon.innerText = '✔';
            copyIcon.classList.add('copied');
            copyIcon.setAttribute('aria-label', 'Copied!');
            setTimeout(() => {
                copyIcon.innerText = '📋';
                copyIcon.classList.remove('copied');
                copyIcon.setAttribute('aria-label', 'Copy to clipboard');
            }, 2000);
        }
    }).catch(err => {
        console.error('Failed to copy text:', err);
    });
}

function toggleSidebar() {
    var sidebar = document.getElementById("sidebar");
    if (sidebar.style.width === "250px") {
        sidebar.style.width = "0";
    } else {
        sidebar.style.width = "250px";
    }
}

