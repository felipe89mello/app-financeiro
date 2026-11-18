// Pequenas melhorias de formulário reaproveitadas em várias páginas do app:
// 1) filtro automático da categoria pelo tipo (despesa/ganho) selecionado;
// 2) um campo de busca com filtro por texto por cima de um <select> comum
//    (digitar "m" mostra só as opções que contêm "m").
// Tudo em JS puro, sem bibliotecas — o app precisa continuar funcionando
// sozinho depois de empacotado com PyInstaller.

function initFiltroTipoCategoria(tipoId, categoriaId) {
  var tipoSel = document.getElementById(tipoId);
  var catSel = document.getElementById(categoriaId);
  if (!tipoSel || !catSel) return;

  function aplicar() {
    var tipo = tipoSel.value;
    var valorAtual = catSel.value;
    var primeiraVisivel = null;

    Array.from(catSel.options).forEach(function (opt) {
      var mostra = opt.dataset.tipo === tipo;
      opt.hidden = !mostra;
      opt.disabled = !mostra;
      if (mostra && !primeiraVisivel) primeiraVisivel = opt;
    });

    var aindaVisivel = Array.from(catSel.options).some(function (o) {
      return o.value === valorAtual && !o.hidden;
    });
    if (!aindaVisivel && primeiraVisivel) {
      catSel.value = primeiraVisivel.value;
    }

    // Avisa o combobox (se essa select tiver um) que as opções mudaram,
    // pra ele atualizar o texto mostrado no campo de busca.
    catSel.dispatchEvent(new Event('options-changed'));
  }

  tipoSel.addEventListener('change', aplicar);
  aplicar();
}

(function () {
  function wrapCombobox(select) {
    if (select.dataset.comboboxInit) return;
    select.dataset.comboboxInit = '1';

    var wrapper = document.createElement('div');
    wrapper.className = 'combobox-wrap';

    var input = document.createElement('input');
    input.type = 'text';
    input.className = 'combobox-input';
    input.autocomplete = 'off';
    input.placeholder = select.dataset.placeholder || 'Digite para buscar...';

    var lista = document.createElement('ul');
    lista.className = 'combobox-lista';
    lista.hidden = true;

    select.parentNode.insertBefore(wrapper, select);
    wrapper.appendChild(input);
    wrapper.appendChild(lista);
    wrapper.appendChild(select);
    select.classList.add('combobox-select-oculto');
    select.tabIndex = -1;

    var indiceAtivo = -1;

    function opcoesVisiveis() {
      return Array.from(select.options).filter(function (o) { return !o.hidden; });
    }

    function textoSelecionado() {
      var opt = select.options[select.selectedIndex];
      return opt ? opt.text : '';
    }

    function marcarAtiva() {
      Array.from(lista.children).forEach(function (li, i) {
        li.classList.toggle('destaque', i === indiceAtivo);
      });
    }

    function renderLista(filtro) {
      lista.innerHTML = '';
      indiceAtivo = -1;
      var termo = (filtro || '').toLowerCase();
      var opcoes = opcoesVisiveis().filter(function (o) {
        return o.text.toLowerCase().indexOf(termo) !== -1;
      });

      if (opcoes.length === 0) {
        var vazio = document.createElement('li');
        vazio.className = 'combobox-vazio';
        vazio.textContent = 'Nenhuma opção encontrada';
        lista.appendChild(vazio);
        return;
      }

      opcoes.forEach(function (opt) {
        var li = document.createElement('li');
        li.textContent = opt.text;
        li.dataset.value = opt.value;
        if (opt.value === select.value) li.classList.add('ativa');
        li.addEventListener('mousedown', function (e) {
          e.preventDefault(); // não deixa o input perder o foco antes do clique registrar
          escolher(opt.value, opt.text);
        });
        lista.appendChild(li);
      });
    }

    function escolher(valor, texto) {
      select.value = valor;
      input.value = texto;
      lista.hidden = true;
      select.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function abrir() {
      renderLista(input.value === textoSelecionado() ? '' : input.value);
      lista.hidden = false;
    }

    input.addEventListener('focus', function () {
      input.select();
      abrir();
    });
    input.addEventListener('input', abrir);
    input.addEventListener('blur', function () {
      // Pequeno atraso pra dar tempo do "mousedown" da lista ser processado
      // antes de fechar e restaurar o texto.
      setTimeout(function () {
        input.value = textoSelecionado();
        lista.hidden = true;
      }, 120);
    });
    input.addEventListener('keydown', function (e) {
      var itens = Array.from(lista.children).filter(function (li) {
        return !li.classList.contains('combobox-vazio');
      });
      if (e.key === 'Escape') {
        input.value = textoSelecionado();
        lista.hidden = true;
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (lista.hidden) { abrir(); return; }
        indiceAtivo = Math.min(indiceAtivo + 1, itens.length - 1);
        marcarAtiva();
        if (itens[indiceAtivo]) itens[indiceAtivo].scrollIntoView({ block: 'nearest' });
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        indiceAtivo = Math.max(indiceAtivo - 1, 0);
        marcarAtiva();
        if (itens[indiceAtivo]) itens[indiceAtivo].scrollIntoView({ block: 'nearest' });
      } else if (e.key === 'Enter') {
        e.preventDefault();
        var alvo = itens[indiceAtivo] || itens[0];
        if (alvo) escolher(alvo.dataset.value, alvo.textContent);
      }
    });

    select.addEventListener('options-changed', function () {
      input.value = textoSelecionado();
    });

    input.value = textoSelecionado();
  }

  window.initCombobox = function (id) {
    var sel = document.getElementById(id);
    if (sel) wrapCombobox(sel);
  };
})();
