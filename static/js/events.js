// Atualiza os cards consumindo nossa própria API REST com Fetch (AJAX).
const refreshButton = document.querySelector("#refreshEvents");
const eventsStatus = document.querySelector("#eventsStatus");
if (refreshButton) {
  refreshButton.addEventListener("click", async () => {
    eventsStatus.textContent = "Atualizando eventos...";
    try {
      const response = await fetch("/api/events");
      if (!response.ok) throw new Error(`Falha HTTP: ${response.status}`);
      const payload = await response.json();
      eventsStatus.textContent = `${payload.count} evento(s) encontrado(s) na API. Atualize a página para recarregar os cards.`;
    } catch (error) {
      eventsStatus.textContent = "Não foi possível atualizar a agenda. Tente novamente.";
      console.error(error);
    }
  });
}

// API pública externa: BrasilAPI fornece feriados nacionais.
const holidayList = document.querySelector("#holidayList");
const holidayState = document.querySelector("#holidayState");
const holidayYear = document.querySelector("#holidayYear");
if (holidayList) {
  const year = new Date().getFullYear();
  holidayYear.textContent = year;
  async function loadHolidays() {
    try {
      const response = await fetch(`https://brasilapi.com.br/api/feriados/v1/${year}`);
      if (!response.ok) throw new Error(`Falha HTTP: ${response.status}`);
      const holidays = await response.json();
      holidayList.replaceChildren();
      holidays.slice(0, 8).forEach((holiday) => {
        const li = document.createElement("li");
        const date = document.createElement("b");
        const name = document.createElement("span");
        date.textContent = holiday.date.split("-").reverse().join("/");
        name.textContent = holiday.name;
        li.append(date, name);
        holidayList.append(li);
      });
      holidayState.textContent = `${holidays.length} datas`;
    } catch (error) {
      holidayState.textContent = "Indisponível";
      holidayList.innerHTML = "<li>Não foi possível carregar os feriados. Tente novamente mais tarde.</li>";
      console.error("Erro ao consultar BrasilAPI:", error);
    }
  }
  loadHolidays();
}