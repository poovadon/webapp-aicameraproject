function activeShowPage() {
    console.log("activeShowPage called");
    setTimeout(showPage, 3000);
}

function showPage() {
    console.log("showPage called");
    $("#preLoader").css({ visibility: "hidden", opacity: 0 }); /* ซ่อน preLoader */
    $("#pageContent").css({ visibility: "visible", opacity: 1 }); /* แสดง pageContent */
}