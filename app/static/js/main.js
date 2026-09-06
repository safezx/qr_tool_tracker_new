// Немного прогрессивного улучшения — сайт полностью работает и без JS
// (все действия идут через обычные HTML-формы), это только удобства.

document.addEventListener("DOMContentLoaded", function () {
  // Подтверждение перед необратимыми действиями (удаление и т.п.)
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!window.confirm(form.dataset.confirm)) {
        event.preventDefault();
      }
    });
  });

  // Автоотправка формы фильтров при смене select'а — без этого пришлось
  // бы нажимать отдельную кнопку "Применить" после каждого выбора.
  document.querySelectorAll("select[data-autosubmit]").forEach(function (select) {
    select.addEventListener("change", function () {
      select.form.submit();
    });
  });
});
