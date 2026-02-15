const getCookie = (name) => {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};

document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("checkout-button");
    console.log("Button found:", button);
    
    if (!button) {
        console.error("Checkout button not found");
        return;
    }

    const configUrl = button.dataset.configUrl;
    const sessionUrl = button.dataset.sessionUrl;
    
    console.log("Config URL:", configUrl);
    console.log("Session URL:", sessionUrl);

    fetch(configUrl)
        .then((result) => {
            console.log("Config response status:", result.status);
            return result.json();
        })
        .then((data) => {
            console.log("Config data:", data);
            
            if (!data.publicKey) {
                console.error("No publicKey in response");
                return;
            }
            
            const stripe = Stripe(data.publicKey);
            console.log("Stripe initialized");

            button.addEventListener("click", () => {
                console.log("Checkout button clicked");
                button.disabled = true;
                button.innerHTML = "Procesando...";

                fetch(sessionUrl, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCookie("csrftoken")
                    },
                    body: JSON.stringify({})
                })
                    .then((res) => {
                        console.log("Session response status:", res.status);
                        return res.json();
                    })
                    .then((data) => {
                        console.log("Session data:", data);
                        
                        if (data.sessionId) {
                            console.log("Redirecting to Stripe Checkout with session:", data.sessionId);
                            return stripe.redirectToCheckout({ sessionId: data.sessionId });
                        } else if (data.error) {
                            alert("Error: " + data.error);
                            button.disabled = false;
                            button.innerHTML = "Pagar con Stripe";
                        } else {
                            alert("Error desconocido al procesar el pago");
                            button.disabled = false;
                            button.innerHTML = "Pagar con Stripe";
                        }
                    })
                    .catch((error) => {
                        console.error("Fetch error:", error);
                        alert("Error de conexión: " + error.message);
                        button.disabled = false;
                        button.innerHTML = "Pagar con Stripe";
                    });
            });
        })
        .catch((error) => {
            console.error("Config fetch error:", error);
            alert("Error al cargar la configuración de pago: " + error.message);
        });
});