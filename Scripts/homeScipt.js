//all this does is control the project hover image change

let pg = document.getElementById("pg")
pg.addEventListener("mouseenter", () => { ChangeImage("pgstrategythumbnail.png")})
pg.addEventListener("mouseleave", () => { ResetImage()})


let gigapay = document.getElementById("gigapay")
gigapay.addEventListener("mouseenter", () => { ChangeImage("gigadesignthumbnail.png")})
gigapay.addEventListener("mouseleave", () => { ResetImage()})


let snow = document.getElementById("snow")
snow.addEventListener("mouseenter", () => { ChangeImage("a.svg")})
snow.addEventListener("mouseleave", () => { ResetImage()})


let leikir = document.getElementById("leikir")
leikir.addEventListener("mouseenter", () => { ChangeImage("b.svg")})
leikir.addEventListener("mouseleave", () => { ResetImage()})


let biekos = document.getElementById("biekos")
biekos.addEventListener("mouseenter", () => { ChangeImage("a.svg")})
biekos.addEventListener("mouseleave", () => { ResetImage()})



let image = document.getElementById("project-image")

function ChangeImage(name) {
    
    console.log(name)
    image.src = "./Assets/Home/" + name

}
function ResetImage() {
    console.log("closed")
    image.src = "./Assets/Home/Project-placeholder.svg"
}

