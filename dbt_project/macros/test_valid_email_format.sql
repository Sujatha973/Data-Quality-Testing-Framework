{% test valid_email_format(model, column_name) %}
-- Custom generic test: flags any row where the column doesn't look like
-- a well-formed email address (basic regex: text@text.text).

select *
from {{ model }}
where {{ column_name }} is not null
  and {{ column_name }} !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

{% endtest %}
