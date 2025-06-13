import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from minimal_viewer import minimal_viewer

    mo.md("# 🧪 Minimal JavaScript Test")
    return minimal_viewer, mo


@app.cell
def _(minimal_viewer):
    # Test minimal viewer
    viewer = minimal_viewer()
    viewer
    return


@app.cell
def _(mo):
    mo.md("""✅ Wenn du das siehst, funktioniert das JavaScript!""")
    return


if __name__ == "__main__":
    app.run()
