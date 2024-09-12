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

function copyToClipboard(codeId) {
    const codeElement = document.getElementById(codeId);
    const text = codeElement.innerText;
    navigator.clipboard.writeText(text).then(() => {
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