/* =========================================================
   NOTIFICATION ENGINE
   - Requests browser permission
   - Checks due dates every 60 seconds
   - Sends reminder alerts
   ========================================================= */

console.log("notifications.js loaded");

// Ask for notification permission
async function requestPermission() {
    if (!("Notification" in window)) return;

    if (Notification.permission === "default") {
        await Notification.requestPermission();
    }
}

// Trigger notification
function pushNotification(title, body) {
    if (Notification.permission === "granted") {
        new Notification(title, { body });
    }
}

// Check all tasks for reminders
function scanDueTasks() {
    const rows = document.querySelectorAll(".todo-row");

    rows.forEach(row => {
        const due = row.dataset.due;
        const title = row.dataset.title;

        if (!due || due === "None" || due.trim() === "") return;

        const now = new Date();
        const dueDate = new Date(due + " 23:59");

        // If deadline is today
        const diff = dueDate - now;

        if (diff > 0 && diff < 1000 * 60 * 60 * 6) { 
            // less than 6 hours left
            pushNotification("⏰ Deadline Soon!", `${title} is due today.`);
        }

        if (diff <= 0) {
            pushNotification("⚠️ Task Overdue!", `${title} is overdue!`);
        }
    });
}

// Start checking
requestPermission();

// Run check every 60 seconds
setInterval(scanDueTasks, 60000);

// Run once on load
setTimeout(scanDueTasks, 2000);
