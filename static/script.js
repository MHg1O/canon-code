function toggle() {
    site = event.srcElement.parentElement.parentElement;
    console.log(site);
    list = site.querySelector("ul.hideable");
    if (list.style.display == "none") {
        list.style.display = "list-item";
        charCode = 8593;
    } else {
        list.style.display = "none";
        charCode = 8595;
    }
    site.querySelector("button").textContent = String.fromCharCode(charCode);
}

function toggleAll() {
    s = document.querySelectorAll("ul[id^='list-']");
    s.forEach(function(item, index) {
        toggle(item.id.slice(5));
    });

    b = document.getElementById("toggle-all");
    if (b.getAttribute("data-status") == "down") {
        b.textContent = String.fromCharCode(8593);
        b.setAttribute("data-status", "up");
    } else {
        b.textContent = String.fromCharCode(8595);
        b.setAttribute("data-status", "down");
    }

}

function processSearch(inp) {
    inp.addEventListener("input", function(e) {
        req = new XMLHttpRequest();
        req.open("GET", "http://localhost:5000/api/search?query=" + encodeURIComponent(this.value));
        req.send();
        console.log(req.response);
    });
}

function revealSearchResult(model_id) {
    document.getElementById("search_result_" + model_id).style.display = "table-cell";
}

function hideSearchResult(model_id) {
    document.getElementById("search_result_" + model_id).style.display = "none";
}
