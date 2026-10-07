// Endereço da API. É ABSOLUTO ("/api"): o navegador pede para o MESMO host da página,
// e o proxy reverso (fase 4) encaminha /api para o container da API.
// Mesmo host = sem problemas de CORS (o navegador não bloqueia).
const API = "/api";

const $ = (id) => document.getElementById(id);
const CAMPOS = ["nome", "especie", "raca", "idade", "tutor"];

// Mostra uma mensagem de sucesso ou erro embaixo do formulário
function avisar(texto, tipo = "ok") {
  $("mensagem").textContent = texto;
  $("mensagem").className = `mensagem ${tipo}`;
}

// Chama a API e trata os erros num lugar só
async function chamarApi(caminho, opcoes = {}) {
  const resp = await fetch(API + caminho, {
    headers: { "Content-Type": "application/json" },
    ...opcoes,
  });
  if (!resp.ok) {
    const corpo = await resp.json().catch(() => ({}));
    // 422 = dados inválidos (validação da API); 404 = não encontrado
    const detalhe = Array.isArray(corpo.detail) ? corpo.detail.map((d) => d.msg).join("; ") : corpo.detail;
    throw new Error(detalhe || `Erro ${resp.status}`);
  }
  return resp.status === 204 ? null : resp.json();
}

// Cria uma célula de tabela com texto. textContent (e não innerHTML) evita que
// alguém cadastre um "nome" com código malicioso (ataque XSS)
function celula(texto) {
  const td = document.createElement("td");
  td.textContent = texto;
  return td;
}

// R: busca a lista na API e desenha a tabela
async function carregarPets() {
  const pets = await chamarApi("/pets");
  const corpo = $("lista-pets");
  corpo.replaceChildren();
  $("vazio").hidden = pets.length > 0;

  for (const pet of pets) {
    const tr = document.createElement("tr");
    tr.append(celula(pet.id), celula(pet.nome), celula(pet.especie),
              celula(pet.raca), celula(pet.idade), celula(pet.tutor));

    const acoes = document.createElement("td");
    const editar = document.createElement("button");
    editar.textContent = "Editar";
    editar.className = "secundario";
    editar.onclick = () => preencherFormulario(pet);

    const excluir = document.createElement("button");
    excluir.textContent = "Excluir";
    excluir.className = "perigo";
    excluir.onclick = () => excluirPet(pet);

    acoes.append(editar, excluir);
    tr.append(acoes);
    corpo.append(tr);
  }
}

// Coloca os dados de um pet no formulário (modo edição)
function preencherFormulario(pet) {
  $("pet-id").value = pet.id;
  CAMPOS.forEach((c) => ($(c).value = pet[c]));
  $("titulo-form").textContent = `Editando: ${pet.nome}`;
  $("btn-salvar").textContent = "Salvar alterações";
  $("btn-cancelar").hidden = false;
  $("nome").focus();
}

// Volta o formulário para o modo "novo pet"
function limparFormulario() {
  $("form-pet").reset();
  $("pet-id").value = "";
  $("titulo-form").textContent = "Novo pet";
  $("btn-salvar").textContent = "Cadastrar";
  $("btn-cancelar").hidden = true;
}

// C e U: se tem id, atualiza (PUT); se não tem, cadastra (POST)
async function salvarPet(evento) {
  evento.preventDefault();
  const dados = Object.fromEntries(CAMPOS.map((c) => [c, $(c).value.trim()]));
  dados.idade = Number(dados.idade);
  const id = $("pet-id").value;

  try {
    if (id) {
      await chamarApi(`/pets/${id}`, { method: "PUT", body: JSON.stringify(dados) });
      avisar(`${dados.nome} atualizado!`);
    } else {
      await chamarApi("/pets", { method: "POST", body: JSON.stringify(dados) });
      avisar(`${dados.nome} cadastrado!`);
    }
    limparFormulario();
    await carregarPets();
  } catch (erro) {
    avisar(`Não foi possível salvar: ${erro.message}`, "erro");
  }
}

// D: pede confirmação e apaga
async function excluirPet(pet) {
  if (!confirm(`Excluir ${pet.nome}?`)) return;
  try {
    await chamarApi(`/pets/${pet.id}`, { method: "DELETE" });
    avisar(`${pet.nome} excluído.`);
    await carregarPets();
  } catch (erro) {
    avisar(`Não foi possível excluir: ${erro.message}`, "erro");
  }
}

// Mostra no topo se a API está respondendo (usa a rota /health)
async function verificarApi() {
  try {
    const saude = await chamarApi("/health");
    $("status-api").textContent = `API online · v${saude.versao}`;
    $("status-api").className = "status online";
    return true;
  } catch {
    $("status-api").textContent = "API indisponível";
    $("status-api").className = "status offline";
    return false;
  }
}

// Início: liga os botões e carrega a lista
$("form-pet").addEventListener("submit", salvarPet);
$("btn-cancelar").addEventListener("click", limparFormulario);
verificarApi().then((online) => {
  if (online) carregarPets();
  else avisar("Não consegui falar com a API em /api. Ela está no ar e atrás do proxy?", "erro");
});
