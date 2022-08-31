SELECT 
    date_format(from_unixtime(timestamp / 1000e0), '%Y-%m-%d %T') as time, 
    httprequest.httpmethod, httprequest.uri, label.name, action, labels, httprequest
FROM 
    '${database_name}.${table_name}',
    UNNEST(labels) as t(label)
ORDER BY label.name, uri;
