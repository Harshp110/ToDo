/* =========================================================
   MAIN FRONTEND LOGIC
   - Drag & Drop reorder (SortableJS)
   - Search + Category Filter
   - Toggle task complete
   ========================================================= */

console.log("main.js loaded");

// 1️⃣ --- SEARCH + CATEGORY FILTER ---
const searchBox = document.getElementById("searchBox");
const filterCat = document.getElementById("filterCategory");
const clearBtn = document.getElementById("clearBtn");

function applyFilters() {
    const q = searchBox.value.trim().toLowerCase();
    const c = filterCat.value;

    document.querySelectorAll(".todo-row").forEach(li => {
        const title = li.dataset.title || "";
        const desc = li.dataset.desc || "";
        const cat = li.dataset.cat || "";

        const match = (title.includes(q) || desc.includes(q)) && (!c || cat === c);
        li.style.display = match ? "" : "none";
    });
}

if (searchBox) searchBox.addEventListener("input", applyFilters);
if (filterCat) filterCat.addEventListener("change", applyFilters);
if (clearBtn) {
    clearBtn.addEventListener("click", () => {
        searchBox.value = "";
        filterCat.value = "";
        applyFilters();
    });
}


// 2️⃣ --- TOGGLE COMPLETED STATUS ---
document.querySelectorAll(".toggle").forEach(cb => {
    cb.addEventListener("change", async (e) => {
        const li = cb.closest("li");
        const sno = li.dataset.sno;

        await fetch("/toggle/" + sno, { method: "POST" });

        if (cb.checked) {
            li.classList.add("bg-light", "opacity-75");
        } else {
            li.classList.remove("bg-light", "opacity-75");
        }
    });
});


// 3️⃣ --- DRAG & DROP SORTING (using SortableJS) ---
const list = document.getElementById("todoList");
if (list) {
    const sortable = new Sortable(list, {
        animation: 150,
        onEnd: function(evt) {
            const order = Array.from(list.querySelectorAll("li"))
                               .map(li => li.dataset.sno);

            fetch("/reorder", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ order })
            });
        }
    });
}

