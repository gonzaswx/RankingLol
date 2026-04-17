let previous = [];

function getRankIcon(tier) {
    if (!tier || tier === "UNRANKED") return "https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-shared-components/global/default/images/provisional.png";
    return `https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-shared-components/global/default/images/${tier.toLowerCase()}.png`;
}

function getProfileIcon(id) { return `https://ddragon.leagueoflegends.com/cdn/14.24.1/img/profileicon/${id}.png`; }

async function load() {
    try {
        const res = await fetch("/ranking");
        const data = await res.json();
        const container = document.getElementById("ranking");
        container.innerHTML = "";

        data.forEach((p, i) => {
            const div = document.createElement("div");
            div.className = "card";
            if (previous.length > 0) {
                const old = previous.findIndex(x => x.name === p.name);
                if (old !== -1) {
                    if (old > i) div.classList.add("up");
                    else if (old < i) div.classList.add("down");
                }
            }

            div.innerHTML = `
                <div class="left">
                    <img class="icon" src="${getProfileIcon(p.icon)}" onerror="this.src='https://ddragon.leagueoflegends.com/cdn/14.24.1/img/profileicon/29.png'"/>
                    <img class="rank-icon" src="${getRankIcon(p.tier)}"/>
                    <div>
                        <div style="font-weight: bold;">#${i + 1} - ${p.name}</div>
                        <div style="font-size: 0.8em; color: #ccc;">${p.tier} ${p.rank}</div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div style="color: #f1c40f; font-weight: bold;">${p.lp} LP</div>
                    <button onclick="removePlayer('${p.name}')" style="background: none; border: none; color: #555; cursor: pointer; font-size: 12px;">✕</button>
                </div>
            `;
            container.appendChild(div);
        });
        previous = data;
    } catch (e) { console.error(e); }
}

async function addNewPlayer() {
    const name = document.getElementById("playerName").value.trim();
    if (!name.includes("#")) return alert("Formato: Nombre#TAG");
    const res = await fetch("/add-player", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({name}) });
    const result = await res.json();
    if (result.status === "success") { document.getElementById("playerName").value = ""; load(); }
    else alert(result.message);
}

async function removePlayer(name) {
    if (!confirm(`¿Quitar a ${name} del ranking?`)) return;
    const res = await fetch("/remove-player", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({name}) });
    const result = await res.json();
    if (result.status === "success") load();
}

load();
setInterval(load, 60000);