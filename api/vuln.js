// validates if input email and password are correct
function checkLogin(req, db) {
    const sqlQuery =
      "SELECT email FROM credentials WHERE " +
      "email='" + req.body.email + "' AND " +
      "password='" + req.body.password + "'";
  
    db.query(sqlQuery, (err, result) => {
      if (err) {
        return false;
      }
  
      return result.length !== 0;
    });
  }

  const express = require('express')
  var pug = require('pug');
  const app = express()
  
  app.post('/', (req, res) => {
      var input = req.query.username;
      var template = `
  doctype
  html
  head
      title= 'Hello world'
  body
      form(action='/' method='post')
          input#name.form-control(type='text)
          button.btn.btn-primary(type='submit') Submit
      p Hello `+ input
      var fn = pug.compile(template);
      var html = fn();
      res.send(html);
  })