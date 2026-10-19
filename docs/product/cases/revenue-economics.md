# Выручка и economics: открытые данные Buffer

[Open Buffer](https://buffer.com/open) публикует MRR/ARR/ARPU; [annual report 2023](https://buffer.com/shareholders/2023) объясняет связь платящих клиентов и месячного дохода на клиента, а также изменения бизнеса. Это собственные раскрытия компании, не независимый audit и не подтверждение всей unit economics.

Для reusable case не копируем постоянно меняющиеся dashboard totals. При конкретном исследовании сохранить дату метрики, определение, период, единицу paid account/user и ссылку. Если дата dashboard data не видна, указать отдельно retrieval date и неизвестный as-of. Проверить округление и coverage, а не объявлять противоречием приблизительное несовпадение ARR и 12×MRR.

Наша адаптация: искать прямые раскрытия прежде моделей и восстанавливать economic bridge по сопоставимым данным. `MRR = paid_accounts × monthly_ARPA` — только при одной и той же базе, валюте и period. MAU не равен paid_accounts. ARR — annualized run rate, не автоматически recognized revenue за прошлый год. Новый рост MRR не гарантирует положительный cash flow.

Для частного конкурента без раскрытий допустим честный «выручка неизвестна». Public traffic не раскрывает paid base, churn, скидки или enterprise/offline sales. Диапазон собственной модели — scenario, не факт о компании. Buffer показывает возможность прозрачности, а не разрешение переносить его conversion/ARPA на другие продукты. Контракт: [revenue](../revenue.md).
