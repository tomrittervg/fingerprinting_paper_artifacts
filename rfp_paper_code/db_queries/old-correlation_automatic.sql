select
  a1.metric1 as A,
  a1.value1 as a,
  'XXX',
  a1.metric2 as B,
  a1.value2 as b, 
  a1.occurrences,
  a1.total_occurrences_for_value1,
  a1.percentage,
  a2.value2 as b_, 
  a2.occurrences,
  a2.total_occurrences_for_value1,
  a2.percentage,
  'XXX',
  a3.value1 as a_,
  a3.value2 as b_, 
  a3.occurrences,
  a3.total_occurrences_for_value1,
  a3.percentage,
  'XXX',
  a4.value1 as a_,
  a4.value2 as b,
  a4.occurrences,
  a4.total_occurrences_for_value1,
  a4.percentage,
  Concat('When ', a1.metric1, ' is ', a1.value1, ' then ', a1.metric2, ' is ', a1.percentage, '% likely to be ', a1.value2) as t1,
  case
    when a2.percentage is null then  Concat('and it is never ', a3.value2, '.')
    else Concat('and ', a2.percentage, '% likely to be ', a2.value2, '.')
  end as t2,
  Concat('But when ', a3.metric1, ' is ', a3.value1, ' then ', a3.metric2, ' is ', a3.percentage, '% likely to be ', a3.value2),
  case
    when a4.percentage is null then  Concat('and it is never ', a1.value2, '.')
    else Concat('and ', a4.percentage, '% likely to be ', a4.value2, '.')
  end,
  
  
from `PROJECT.fpanalysis.UserCharacteristics_x_by_y_tbl` a1

left outer join `PROJECT.fpanalysis.UserCharacteristics_x_by_y_tbl` a2
  on a1.metric1 = a2.metric1
  and a1.value1 = a2.value1
  and a1.metric2 = a2.metric2
  and a1.value2 <> a2.value2

inner join `PROJECT.fpanalysis.UserCharacteristics_x_by_y_tbl` a3
  on a1.metric1 = a3.metric1
  and a1.value1 <> a3.value1
  and a1.metric2 = a3.metric2
  and (
      a2.value2 = a3.value2
      or 
        (
          a2.value2 is null
          and
          a1.value2 <> a3.value2 -- if a2.value2 is not null, this is already covered
        )
  )

left outer join `PROJECT.fpanalysis.UserCharacteristics_x_by_y_tbl` a4
  on a1.metric1 = a4.metric1
  and a3.value1 = a4.value1
  and a1.metric2 = a4.metric2
  and a4.value2 = a1.value2

where 
    1 = 1

/* Limit ourselves to highly correlated a and b values that occur at least a few times. */
and a1.percentage > 98
and a1.total_occurrences_for_value1 > 50

/*
Do not include this clause.  
Without this clause you will get _all_ of the b' (b != b') for a - and if there are no results, you know there is no such b' value that ever appears for a
However if you include this clause you might miss a b' value for a if it does actually occur a lot.
and (
  a2.percentage is null
  or
  a2.percentage < 2
)
*/

/* Limit ourselves to highly correlated a' and b' values that occur at least a few times. */
and a3.percentage > 98
and a3.total_occurrences_for_value1 > 50

/*
Do not include this clause for the same reason
and (
  a4.percentage < 2
  or
  a4.percentage is null
)
*/


and a1.metric1 not like 'characteristics_cpu_model'

and a1.metric1  not like '%_gl_%'
and a1.metric2  not like '%_gl_%'

and a1.metric1 not like 'characteristics_canvas%'
and a1.metric1 not like 'characteristics_avail_height%'

order by a1.total_occurrences_for_value1 desc



delete
from PROJECT.fpanalysis.Correlations_x_by_y_98th_percentile_min_50_tbl 
where 
(
	a_metric = 'gl_renderer_raw'
and  b_metric = 'gl2_renderer_raw'
and a = b
and b_percentage_of_total_a_values = 100
) or (
	a_metric = 'gl2_renderer_raw'
and  b_metric = 'gl_renderer_raw'
and a = b
and b_percentage_of_total_a_values = 100
) or 
-------------------------------------------
(
	a_metric = 'gl_renderer_raw'
and  b_metric = 'gl_vendor'
and b_percentage_of_total_a_values = 100
) or (
	a_metric = 'gl2_renderer_raw'
and  b_metric = 'gl_vendor'
and b_percentage_of_total_a_values = 100
) or 
-------------------------------------------
(
	a_metric = 'gl_renderer_raw'
and  b_metric = 'gl_vendor_raw'
and b_percentage_of_total_a_values = 100
) or (
	a_metric = 'gl2_renderer_raw'
and  b_metric = 'gl_vendor_raw'
and b_percentage_of_total_a_values = 100
) 