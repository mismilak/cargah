$(document).ready(function() {
    // تابع بررسی عدد بودن
    function isNumber(n) {
        return !isNaN(parseFloat(n)) && isFinite(n);
    }

    // تابع تنظیم اندازه فونت
    function setFontSize(el) {
        var fontSize = el.val();

        if (isNumber(fontSize) && fontSize >= 0.5) {
            $('body').css({ fontSize: fontSize + 'em' });
        } else if (fontSize) {
            el.val('1');
            $('body').css({ fontSize: '1em' });
        }
    }

    // رویدادهای تغییر اندازه فونت
    $('#fontSize')
        .on('change', function() { setFontSize($(this)); })
        .on('keyup', function(e) {
            if (e.keyCode == 27) {
                $(this).val('1');
                $('body').css({ fontSize: '1em' });
            } else {
                setFontSize($(this));
            }
        });

    // رویداد کلیک ESC در سطح پنجره
    $(window).on('keyup', function(e) {
        if (e.keyCode == 27) {
            $('#fontSize').val('1');
            $('body').css({ fontSize: '1em' });
        }
    });

    // آبجکت treeview با توابع اصلاح شده
    let treeview = {
        // تابع ریست دکمه‌ها
        resetBtnToggle: function() {
            $(".js-treeview")
                .find(".level-add")
                .find("span")
                .removeClass()
                .addClass("fa fa-plus");
            $(".js-treeview")
                .find(".level-add")
                .siblings()
                .removeClass("in");
        },

        // تابع اضافه کردن سطح هم‌تراز
        addSameLevel: function(target) {
            let ulElm = target.closest("ul");
            let levelElement = target.closest("[data-level]");

            if (levelElement.length && levelElement.attr("data-level")) {
                let sameLevelCodeASCII = levelElement.attr("data-level").charCodeAt(0);
                ulElm.append($("#levelMarkup").html());
                ulElm.children("li:last-child")
                    .find("[data-level]")
                    .attr("data-level", String.fromCharCode(sameLevelCodeASCII));
            } else {
                console.error("Element with data-level attribute not found");
            }
        },

        // تابع اضافه کردن سطح زیرین (اصلاح شده)
        addSubLevel: function(target) {
            let liElm = target.closest("li");
            let levelElement = liElm.find("[data-level]");

            if (levelElement.length && levelElement.attr("data-level")) {
                let nextLevelCodeASCII = levelElement.attr("data-level").charCodeAt(0) + 1;

                // اگر ul فرزند وجود ندارد، یک ul جدید ایجاد کنید
                if (liElm.children("ul").length === 0) {
                    liElm.append("<ul></ul>");
                }

                liElm.children("ul").append($("#levelMarkup").html());
                liElm.children("ul").find("[data-level]")
                    .attr("data-level", String.fromCharCode(nextLevelCodeASCII));
            } else {
                console.error("Element with data-level attribute not found");
            }
        },

        // تابع حذف سطح
        removeLevel: function(target) {
            target.closest("li").remove();
        }
    };

    // رویدادهای treeview
    $(".js-treeview")
        // کلیک روی دکمه افزودن
        .on("click", ".level-add", function() {
            $(this).find("span").toggleClass("fa-plus").toggleClass("fa-times text-danger");
            $(this).siblings().toggleClass("in");
        })

        // اضافه کردن سطح هم‌تراز
        .on("click", ".level-same", function() {
            treeview.addSameLevel($(this));
            treeview.resetBtnToggle();
        })

        // اضافه کردن سطح زیرین
        .on("click", ".level-sub", function() {
            treeview.addSubLevel($(this));
            treeview.resetBtnToggle();
        })

        // حذف سطح
        .on("click", ".level-remove", function() {
            treeview.removeLevel($(this));
        })

        // انتخاب سطح
        .on("click", ".level-title", function() {
            let isSelected = $(this).closest("[data-level]").hasClass("selected");
            !isSelected && $(this).closest(".js-treeview").find("[data-level]").removeClass("selected");
            $(this).closest("[data-level]").toggleClass("selected");
        });
});