# MyAuto Landing

Одностраничный лендинг, публикуется бесплатно на [GitHub Pages](https://pages.github.com/).

## Локальный просмотр

```bash
cd "MyAuto Landing"
python3 -m http.server 8080
```

Откройте http://localhost:8080

## Публикация на GitHub Pages

### 1. Создайте репозиторий на GitHub

1. [github.com/new](https://github.com/new)
2. Имя, например: `myauto-landing`
3. **Public** (Pages бесплатно для public-репозиториев)
4. Без README, `.gitignore` и лицензии — они уже в проекте

### 2. Загрузите код

```bash
cd "/Users/iazotov/Documents/Cursor projects/MyAuto Landing"
git remote add origin https://github.com/ВАШ_ЛОГИН/myauto-landing.git
git branch -M main
git push -u origin main
```

### 3. Включите GitHub Pages

1. Репозиторий → **Settings** → **Pages**
2. **Build and deployment** → **Source**: **Deploy from a branch**
3. **Branch**: `main`, папка **`/ (root)`**
4. **Save**

Через 1–2 минуты сайт будет по адресу:

`https://ВАШ_ЛОГИН.github.io/myauto-landing/`

(если репозиторий называется `ВАШ_ЛОГИН.github.io`, сайт откроется с корня: `https://ВАШ_ЛОГИН.github.io`)

## Структура

```
index.html      — страница
css/main.css    — стили
assets/         — изображения, иконки, шрифты
```
