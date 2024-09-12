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
    let childNodes = document.querySelector('#' + codeId).childNodes;
    if (childNodes.length > 1) {
        text = childNodes[1].textContent.trim()
    } else {
        text = document.querySelector('#' + codeId).innerText.trim();
    }
    // copy the text to clipboard
    navigator.clipboard.writeText(text).then(() => {
        // update copy icon style
        const copyIcon = codeElement.parentElement.nextElementSibling;
        copyIcon.innerText = '✔';
        copyIcon.classList.add('copied');
        copyIcon.title = "Command copied to clipboard";
        setTimeout(() => {
            copyIcon.innerText = '📋';
            copyIcon.classList.remove('copied');
            copyIcon.title = "Copy Command";
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}
