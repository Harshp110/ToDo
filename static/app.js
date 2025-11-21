// -------------------------------
//  TOGGLE COMPLETED
// -------------------------------

document.querySelectorAll(".toggle").forEach(box => {
    box.addEventListener("change", () => {
        const id = box.dataset.id;

        fetch("/toggle/" + id, { method: "POST" })
            .then(() => {
                const row = box.closest(".task-row");

                if (box.checked) {
                    row.classList.add("completed-task");
                } else {
                    row.classList.remove("completed-task");
                }
            });
    });
});



// -------------------------------
//  DRAG & DROP REORDER
// -------------------------------

var taskList = document.getElementById("taskList");

if (taskList) {
    new Sortable(taskList, {
        animation: 150,
        ghostClass: 'sortable-ghost',
        chosenClass: 'sortable-chosen',

        onEnd: function () {
            let order = [];
            document.querySelectorAll("#taskList li").forEach((item) => {
                order.push(item.dataset.id);
            });

            fetch("/reorder", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ order: order })
            });
        }
    });
}
