const HEARTBEAT_URL = document.body.dataset.heartbeatUrl;
const UPDATE_INTERVAL = 3000; // toutes les 3 secondes 

// Fonction qui fait battre le cœur
async function heartbeat() {
    try {
        const response = await fetch(HEARTBEAT_URL);
        if (response.ok) {
            const data = await response.json();
            
            // Petit cœur qui bat en vert si l'API est vivante
            const heart = document.querySelector('[data-lucide="heart"]');
            if (heart) {
                heart.classList.remove('text-red-500', 'opacity-50');
                heart.classList.add('text-green-500', 'animate-pulse');
            }
        }
    } catch (err) {
        // Cœur rouge/orange si l'API est down
        const heart = document.querySelector('[data-lucide="heart"]');
        if (heart) {
            heart.classList.remove('text-green-500', 'animate-pulse');
            heart.classList.add('text-red-500', 'opacity-70');
        }
    }
}

// Lancement immédiat + toutes les X secondes
heartbeat();
setInterval(heartbeat, UPDATE_INTERVAL);